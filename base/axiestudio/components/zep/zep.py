from axiestudio.base.memory.model import LCChatMemoryComponent
from axiestudio.field_typing.constants import Memory
from axiestudio.inputs.inputs import DropdownInput, MessageTextInput, SecretStrInput


class ZepChatMemory(LCChatMemoryComponent):
    display_name = "Zep-chattminne"
    description = "Hämtar och lagrar chattmeddelanden från Zep."
    name = "ZepChatMemory"
    icon = "ZepMemory"
    legacy = True

    inputs = [
        MessageTextInput(name="url", display_name="Zep-URL", info="URL för Zep-instansen."),
        SecretStrInput(name="api_key", display_name="API-nyckel", info="API-nyckel för Zep-instansen."),
        DropdownInput(
            name="api_base_path",
            display_name="API-bassökväg",
            options=["api/v1", "api/v2"],
            value="api/v1",
            advanced=True,
        ),
        MessageTextInput(
            name="session_id", display_name="Sessions-ID", info="Sessions-ID för meddelandet.", advanced=True
        ),
    ]

    def build_message_history(self) -> Memory:
        try:
            # Monkeypatch API_BASE_PATH to
            # avoid 404
            # This is a workaround for the local Zep instance
            # cloud Zep works with v2
            import zep_python.zep_client
            from zep_python import ZepClient
            from zep_python.langchain import ZepChatMessageHistory

            zep_python.zep_client.API_BASE_PATH = self.api_base_path
        except ImportError as e:
            msg = "Could not import zep-python package. Please install it with `pip install zep-python`."
            raise ImportError(msg) from e

        zep_client = ZepClient(api_url=self.url, api_key=self.api_key)
        return ZepChatMessageHistory(session_id=self.session_id, zep_client=zep_client)
