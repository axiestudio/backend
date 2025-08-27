import assemblyai as aai
from loguru import logger

from axiestudio.custom.custom_component.component import Component
from axiestudio.field_typing.range_spec import RangeSpec
from axiestudio.io import DataInput, FloatInput, Output, SecretStrInput
from axiestudio.schema.data import Data


class AssemblyAITranscriptionJobPoller(Component):
    display_name = "AssemblyAI Kontrollera transkription"
    description = "Kontrollera statusen för ett transkriptionsjobb med AssemblyAI"
    documentation = "https://www.assemblyai.com/docs"
    icon = "AssemblyAI"

    inputs = [
        SecretStrInput(
            name="api_key",
            display_name="Assembly API-nyckel",
            info="Din AssemblyAI API-nyckel. Du kan få en från https://www.assemblyai.com/",
            required=True,
        ),
        DataInput(
            name="transcript_id",
            display_name="Transkriptions-ID",
            info="ID:t för transkriptionsjobbet att kontrollera",
            required=True,
        ),
        FloatInput(
            name="polling_interval",
            display_name="Kontrollintervall",
            value=3.0,
            info="Kontrollintervallet i sekunder",
            advanced=True,
            range_spec=RangeSpec(min=3, max=30),
        ),
    ]

    outputs = [
        Output(display_name="Transkriptionsresultat", name="transcription_result", method="poll_transcription_job"),
    ]

    def poll_transcription_job(self) -> Data:
        """Polls the transcription status until completion and returns the Data."""
        aai.settings.api_key = self.api_key
        aai.settings.polling_interval = self.polling_interval

        # check if it's an error message from the previous step
        if self.transcript_id.data.get("error"):
            self.status = self.transcript_id.data["error"]
            return self.transcript_id

        try:
            transcript = aai.Transcript.get_by_id(self.transcript_id.data["transcript_id"])
        except Exception as e:  # noqa: BLE001
            error = f"Getting transcription failed: {e}"
            logger.opt(exception=True).debug(error)
            self.status = error
            return Data(data={"error": error})

        if transcript.status == aai.TranscriptStatus.completed:
            json_response = transcript.json_response
            text = json_response.pop("text", None)
            utterances = json_response.pop("utterances", None)
            transcript_id = json_response.pop("id", None)
            sorted_data = {"text": text, "utterances": utterances, "id": transcript_id}
            sorted_data.update(json_response)
            data = Data(data=sorted_data)
            self.status = data
            return data
        self.status = transcript.error
        return Data(data={"error": transcript.error})
