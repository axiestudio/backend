from axiestudio.custom.custom_component.component import Component
from axiestudio.io import (
    MessageTextInput,
    Output,
    SecretStrInput,
)
from axiestudio.schema.data import Data


class ScrapeGraphMarkdownifyApi(Component):
    display_name: str = "ScrapeGraph Markdownify API"
    description: str = "Givet en URL kommer den att returnera det markdownifierade innehållet från webbplatsen."
    name = "ScrapeGraphMarkdownifyApi"

    output_types: list[str] = ["Document"]
    documentation: str = "https://docs.scrapegraphai.com/services/markdownify"

    inputs = [
        SecretStrInput(
            name="api_key",
            display_name="ScrapeGraph API-nyckel",
            required=True,
            password=True,
            info="API-nyckeln för att använda ScrapeGraph API.",
        ),
        MessageTextInput(
            name="url",
            display_name="URL",
            tool_mode=True,
            info="URL:en att markdownifiera.",
        ),
    ]

    outputs = [
        Output(display_name="Data", name="data", method="scrape"),
    ]

    def scrape(self) -> list[Data]:
        try:
            from scrapegraph_py import Client
            from scrapegraph_py.logger import sgai_logger
        except ImportError as e:
            msg = "Could not import scrapegraph-py package. Please install it with `pip install scrapegraph-py`."
            raise ImportError(msg) from e

        # Set logging level
        sgai_logger.set_logging(level="INFO")

        # Initialize the client with API key
        sgai_client = Client(api_key=self.api_key)

        try:
            # Markdownify request
            response = sgai_client.markdownify(
                website_url=self.url,
            )

            # Close the client
            sgai_client.close()

            return Data(data=response)
        except Exception:
            sgai_client.close()
            raise
