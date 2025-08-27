import requests
from pydantic.v1 import SecretStr
from typing_extensions import override

from axiestudio.base.models.model import LCModelComponent
from axiestudio.field_typing import LanguageModel
from axiestudio.field_typing.range_spec import RangeSpec
from axiestudio.inputs.inputs import BoolInput, DictInput, DropdownInput, IntInput, SecretStrInput, SliderInput, StrInput

DEEPSEEK_MODELS = ["deepseek-chat"]


class DeepSeekModelComponent(LCModelComponent):
    display_name = "DeepSeek"
    description = "Generera text med DeepSeek LLM:er."
    icon = "DeepSeek"

    inputs = [
        *LCModelComponent._base_inputs,
        IntInput(
            name="max_tokens",
            display_name="Max tokens",
            advanced=True,
            info="Maximalt antal tokens att generera. Sätt till 0 för obegränsat.",
            range_spec=RangeSpec(min=0, max=128000),
        ),
        DictInput(
            name="model_kwargs",
            display_name="Modell-kwargs",
            advanced=True,
            info="Ytterligare nyckelordsargument att skicka till modellen.",
        ),
        BoolInput(
            name="json_mode",
            display_name="JSON-läge",
            advanced=True,
            info="Om True, kommer det att mata ut JSON oavsett om ett schema skickas.",
        ),
        DropdownInput(
            name="model_name",
            display_name="Modellnamn",
            info="DeepSeek-modell att använda",
            options=DEEPSEEK_MODELS,
            value="deepseek-chat",
            refresh_button=True,
        ),
        StrInput(
            name="api_base",
            display_name="DeepSeek API-bas",
            advanced=True,
            info="Bas-URL för API-förfrågningar. Standard är https://api.deepseek.com",
            value="https://api.deepseek.com",
        ),
        SecretStrInput(
            name="api_key",
            display_name="DeepSeek API-nyckel",
            info="DeepSeek API-nyckeln",
            advanced=False,
            required=True,
        ),
        SliderInput(
            name="temperature",
            display_name="Temperatur",
            info="Styr slumpmässighet i svar",
            value=1.0,
            range_spec=RangeSpec(min=0, max=2, step=0.01),
            advanced=True,
        ),
        IntInput(
            name="seed",
            display_name="Frö",
            info="Fröet styr reproducerbarheten av jobbet.",
            advanced=True,
            value=1,
        ),
    ]

    def get_models(self) -> list[str]:
        if not self.api_key:
            return DEEPSEEK_MODELS

        url = f"{self.api_base}/models"
        headers = {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            model_list = response.json()
            return [model["id"] for model in model_list.get("data", [])]
        except requests.RequestException as e:
            self.status = f"Fel vid hämtning av modeller: {e}"
            return DEEPSEEK_MODELS

    @override
    def update_build_config(self, build_config: dict, field_value: str, field_name: str | None = None):
        if field_name in {"api_key", "api_base", "model_name"}:
            models = self.get_models()
            build_config["model_name"]["options"] = models
        return build_config

    def build_model(self) -> LanguageModel:
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as e:
            msg = "langchain-openai är inte installerat. Vänligen installera med `pip install langchain-openai`"
            raise ImportError(msg) from e

        api_key = SecretStr(self.api_key).get_secret_value() if self.api_key else None
        output = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature if self.temperature is not None else 0.1,
            max_tokens=self.max_tokens or None,
            model_kwargs=self.model_kwargs or {},
            base_url=self.api_base,
            api_key=api_key,
            streaming=self.stream if hasattr(self, "stream") else False,
            seed=self.seed,
        )

        if self.json_mode:
            output = output.bind(response_format={"type": "json_object"})

        return output

    def _get_exception_message(self, e: Exception):
        """Get message from DeepSeek API exception."""
        try:
            from openai import BadRequestError

            if isinstance(e, BadRequestError):
                message = e.body.get("message")
                if message:
                    return message
        except ImportError:
            pass
        return None
