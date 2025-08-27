import json

import httpx
from loguru import logger

from axiestudio.custom.custom_component.component import Component
from axiestudio.io import MessageTextInput, Output
from axiestudio.schema.data import Data


class OlivyaComponent(Component):
    display_name = "Ring samtal"
    description = "En komponent för att skapa en utgående samtalsförfrågan från Olivyas plattform."
    documentation: str = "http://docs.axiestudio.org/components/olivya"
    icon = "Olivya"
    name = "OlivyaComponent"

    inputs = [
        MessageTextInput(
            name="api_key",
            display_name="API-nyckel",
            info="Din API-nyckel för autentisering",
            value="",
            required=True,
        ),
        MessageTextInput(
            name="from_number",
            display_name="Från nummer",
            info="Agentens telefonnummer",
            value="",
            required=True,
        ),
        MessageTextInput(
            name="to_number",
            display_name="Till nummer",
            info="Mottagarens telefonnummer",
            value="",
            required=True,
        ),
        MessageTextInput(
            name="first_message",
            display_name="Första meddelandet",
            info="Agentens introduktionsmeddelande",
            value="",
            required=False,
            tool_mode=True,
        ),
        MessageTextInput(
            name="system_prompt",
            display_name="Systemprompt",
            info="Systemprompten för att guida interaktionen",
            value="",
            required=False,
        ),
        MessageTextInput(
            name="conversation_history",
            display_name="Konversationshistorik",
            info="Sammanfattningen av konversationen",
            value="",
            required=False,
            tool_mode=True,
        ),
    ]

    outputs = [
        Output(display_name="Utdata", name="output", method="build_output"),
    ]

    async def build_output(self) -> Data:
        try:
            payload = {
                "variables": {
                    "first_message": self.first_message.strip() if self.first_message else None,
                    "system_prompt": self.system_prompt.strip() if self.system_prompt else None,
                    "conversation_history": self.conversation_history.strip() if self.conversation_history else None,
                },
                "from_number": self.from_number.strip(),
                "to_number": self.to_number.strip(),
            }

            headers = {
                "Authorization": self.api_key.strip(),
                "Content-Type": "application/json",
            }

            logger.info("Sending POST request with payload: %s", payload)

            # Send the POST request with a timeout
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://phone.olivya.io/create_zap_call",
                    headers=headers,
                    json=payload,
                    timeout=10.0,
                )
                response.raise_for_status()

                # Parse and return the successful response
                response_data = response.json()
                logger.info("Request successful: %s", response_data)

        except httpx.HTTPStatusError as http_err:
            logger.exception("HTTP error occurred")
            response_data = {"error": f"HTTP error occurred: {http_err}", "response_text": response.text}
        except httpx.RequestError as req_err:
            logger.exception("Request failed")
            response_data = {"error": f"Request failed: {req_err}"}
        except json.JSONDecodeError as json_err:
            logger.exception("Response parsing failed")
            response_data = {"error": f"Response parsing failed: {json_err}", "raw_response": response.text}
        except Exception as e:  # noqa: BLE001
            logger.exception("An unexpected error occurred")
            response_data = {"error": f"An unexpected error occurred: {e!s}"}

        # Return the response as part of the output
        return Data(value=response_data)
