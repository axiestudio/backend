from axiestudio.base.embeddings.aiml_embeddings import AIMLEmbeddingsImpl
from axiestudio.base.embeddings.model import LCEmbeddingsModel
from axiestudio.field_typing import Embeddings
from axiestudio.inputs.inputs import DropdownInput
from axiestudio.io import SecretStrInput


class AIMLEmbeddingsComponent(LCEmbeddingsModel):
    display_name = "AI/ML API-inbäddningar"
    description = "Generera inbäddningar med AI/ML API."
    icon = "AIML"
    name = "AIMLEmbeddings"

    inputs = [
        DropdownInput(
            name="model_name",
            display_name="Modellnamn",
            options=[
                "text-embedding-3-small",
                "text-embedding-3-large",
                "text-embedding-ada-002",
            ],
            required=True,
        ),
        SecretStrInput(
            name="aiml_api_key",
            display_name="AI/ML API-nyckel",
            value="AIML_API_KEY",
            required=True,
        ),
    ]

    def build_embeddings(self) -> Embeddings:
        return AIMLEmbeddingsImpl(
            api_key=self.aiml_api_key,
            model=self.model_name,
        )
