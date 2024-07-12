import json
from loguru import logger
from mlserver import MLModel, types
from mlserver.codecs import StringCodec
from mlserver.types import InferenceRequest, InferenceResponse, ResponseOutput
import mlflow


class CustomTransformersModel(MLModel):
    async def load(self) -> bool:
        model_uri = self.settings.parameters.uri
        self.model = mlflow.transformers.load_model(
            model_uri=model_uri, return_type="pipeline", aggregation_strategy="simple"
        )
        self.ready = True
        return self.ready

    async def predict(self, payload: InferenceRequest) -> InferenceResponse:
        # Decode the input text
        logger.info(f"{payload.inputs=}")
        input_texts = StringCodec.decode_input(payload.inputs[0])
        logger.info(f"{input_texts=}")

        # Make predictions
        predictions = self.model(input_texts)
        logger.info(f"{predictions=}")

        for prediction in predictions:
            for item in prediction:
                item["score"] = float(item["score"])
        response_bytes = json.dumps(predictions).encode("UTF-8")

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
