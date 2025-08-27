import requests
from langchain.tools import StructuredTool
from loguru import logger
from pydantic import BaseModel, Field

from axiestudio.base.langchain_utilities.model import LCToolComponent
from axiestudio.field_typing import Tool
from axiestudio.inputs.inputs import SecretStrInput, StrInput
from axiestudio.schema.data import Data


class NotionDatabaseProperties(LCToolComponent):
    display_name: str = "Lista databasegenskaper"
    description: str = "Hämta egenskaper från en Notion-databas."
    documentation: str = "https://docs.axiestudio.org/integrations/notion/list-database-properties"
    icon = "NotionDirectoryLoader"

    inputs = [
        StrInput(
            name="database_id",
            display_name="Databas-ID",
            info="ID:t för Notion-databasen.",
        ),
        SecretStrInput(
            name="notion_secret",
            display_name="Notion-hemlighet",
            info="Notion-integrationstokenet.",
            required=True,
        ),
    ]

    class NotionDatabasePropertiesSchema(BaseModel):
        database_id: str = Field(..., description="The ID of the Notion database.")

    def run_model(self) -> Data:
        result = self._fetch_database_properties(self.database_id)
        if isinstance(result, str):
            # An error occurred, return it as text
            return Data(text=result)
        # Success, return the properties
        return Data(text=str(result), data=result)

    def build_tool(self) -> Tool:
        return StructuredTool.from_function(
            name="notion_database_properties",
            description="Retrieve properties of a Notion database. Input should include the database ID.",
            func=self._fetch_database_properties,
            args_schema=self.NotionDatabasePropertiesSchema,
        )

    def _fetch_database_properties(self, database_id: str) -> dict | str:
        url = f"https://api.notion.com/v1/databases/{database_id}"
        headers = {
            "Authorization": f"Bearer {self.notion_secret}",
            "Notion-Version": "2022-06-28",  # Use the latest supported version
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("properties", {})
        except requests.exceptions.RequestException as e:
            return f"Error fetching Notion database properties: {e}"
        except ValueError as e:
            return f"Error parsing Notion API response: {e}"
        except Exception as e:  # noqa: BLE001
            logger.opt(exception=True).debug("Error fetching Notion database properties")
            return f"An unexpected error occurred: {e}"
