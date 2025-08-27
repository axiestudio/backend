from langchain_openai import AzureChatOpenAI

from axiestudio.base.models.model import LCModelComponent
from axiestudio.field_typing import LanguageModel
from axiestudio.field_typing.range_spec import RangeSpec
from axiestudio.inputs.inputs import MessageTextInput
from axiestudio.io import DropdownInput, IntInput, SecretStrInput, SliderInput


class AzureChatOpenAIComponent(LCModelComponent):
    display_name: str = "Azure OpenAI"
    description: str = "Generera text med Azure OpenAI LLM:er."
    documentation: str = "https://python.langchain.com/docs/integrations/llms/azure_openai"
    beta = False
    icon = "Azure"
    name = "AzureOpenAIModel"

    AZURE_OPENAI_API_VERSIONS = [
        "2024-06-01",
        "2024-07-01-preview",
        "2024-08-01-preview",
        "2024-09-01-preview",
        "2024-10-01-preview",
        "2023-05-15",
        "2023-12-01-preview",
        "2024-02-15-preview",
        "2024-03-01-preview",
        "2024-12-01-preview",
        "2025-01-01-preview",
        "2025-02-01-preview",
    ]

    inputs = [
        *LCModelComponent._base_inputs,
        MessageTextInput(
            name="azure_endpoint",
            display_name="Azure-endpoint",
            info="Din Azure-endpoint, inklusive resursen. Exempel: `https://example-resource.azure.openai.com/`",
            required=True,
        ),
        MessageTextInput(name="azure_deployment", display_name="Distributionsnamn", required=True),
        SecretStrInput(name="api_key", display_name="API-nyckel", required=True),
        DropdownInput(
            name="api_version",
            display_name="API-version",
            options=sorted(AZURE_OPENAI_API_VERSIONS, reverse=True),
            value=next(
                (
                    version
                    for version in sorted(AZURE_OPENAI_API_VERSIONS, reverse=True)
                    if not version.endswith("-preview")
                ),
                AZURE_OPENAI_API_VERSIONS[0],
            ),
        ),
        SliderInput(
            name="temperature",
            display_name="Temperatur",
            value=0.7,
            range_spec=RangeSpec(min=0, max=2, step=0.01),
            info="Styr slumpmässighet. Lägre värden är mer deterministiska, högre värden är mer kreativa.",
            advanced=True,
        ),
        IntInput(
            name="max_tokens",
            display_name="Max tokens",
            advanced=True,
            info="Maximalt antal tokens att generera. Sätt till 0 för obegränsade tokens.",
        ),
    ]

    def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        azure_endpoint = self.azure_endpoint
        azure_deployment = self.azure_deployment
        api_version = self.api_version
        api_key = self.api_key
        temperature = self.temperature
        max_tokens = self.max_tokens
        stream = self.stream

        try:
            output = AzureChatOpenAI(
                azure_endpoint=azure_endpoint,
                azure_deployment=azure_deployment,
                api_version=api_version,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens or None,
                streaming=stream,
            )
        except Exception as e:
            msg = f"Kunde inte ansluta till AzureOpenAI API: {e}"
            raise ValueError(msg) from e

        return output
