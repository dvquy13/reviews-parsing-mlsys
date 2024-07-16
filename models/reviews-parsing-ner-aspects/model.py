import json
from loguru import logger
from mlserver import MLModel, types
from mlserver.codecs import StringCodec
from mlserver.types import InferenceRequest, InferenceResponse, ResponseOutput
import mlflow

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

trace.set_tracer_provider(
    TracerProvider(
        resource=Resource.create({SERVICE_NAME: "reviews-parsing-ner-aspects-mlserver"})
    )
)
tracer = trace.get_tracer(__name__)

# create a JaegerExporter
jaeger_exporter = JaegerExporter(
    # configure agent
    agent_host_name="jaeger",
    agent_port=6831,
    # optional: configure also collector
    # collector_endpoint='http://localhost:14268/api/traces?format=jaeger.thrift',
    # username=xxxx, # optional
    # password=xxxx, # optional
    # max_tag_value_length=None # optional
)

# Create a BatchSpanProcessor and add the exporter to it
span_processor = BatchSpanProcessor(jaeger_exporter)

# Add to the tracer
trace.get_tracer_provider().add_span_processor(span_processor)


class CustomTransformersModel(MLModel):
    async def load(self) -> bool:
        model_uri = self.settings.parameters.uri
        self.model = mlflow.transformers.load_model(
            model_uri=model_uri, return_type="pipeline", aggregation_strategy="simple"
        )
        self.ready = True
        return self.ready

    async def predict(self, payload: InferenceRequest) -> InferenceResponse:
        with tracer.start_as_current_span("make-prediction"):
            with tracer.start_as_current_span("parse-input") as span:
                # Decode the input text
                logger.info(f"{payload.inputs=}")
                span.set_attribute("payload.inputs.shape", payload.inputs[0].shape)
                input_texts = StringCodec.decode_input(payload.inputs[0])
                logger.info(f"{input_texts=}")

                # Make predictions
            with tracer.start_as_current_span("predict") as span:
                predictions = self.model(input_texts)
                logger.info(f"{predictions=}")

                for prediction in predictions:
                    for item in prediction:
                        item["score"] = float(item["score"])
                response_bytes = json.dumps(predictions).encode("UTF-8")

            with tracer.start_as_current_span("format-output") as span:
                # Prepare the response
                response = ResponseOutput(
                    name="predictions",
                    shape=[len(predictions)],
                    datatype="BYTES",
                    data=response_bytes,
                )

                return InferenceResponse(
                    model_name=self.name,
                    model_version=self.version,
                    outputs=[response],
                    parameters=types.Parameters(content_type="application/json"),
                )
