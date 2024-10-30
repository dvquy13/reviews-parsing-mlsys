import json
import os

import mlflow
from loguru import logger
from mlserver import MLModel, types
from mlserver.codecs import StringCodec
from mlserver.types import InferenceRequest, InferenceResponse, ResponseOutput
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Service name is required for most backends
resource = Resource(attributes={SERVICE_NAME: "rpna-mlserver"})
jaeger_url = os.environ.get("JAEGER_URL")

traceProvider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{jaeger_url}/v1/traces"))
traceProvider.add_span_processor(processor)
trace.set_tracer_provider(traceProvider)
tracer = trace.get_tracer(__name__)


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

            with tracer.start_as_current_span("predict") as span:
                # Make predictions
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
