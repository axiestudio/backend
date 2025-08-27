import re

import requests
from bs4 import BeautifulSoup
from langchain_community.document_loaders import RecursiveUrlLoader
from loguru import logger

from axiestudio.custom.custom_component.component import Component
from axiestudio.field_typing.range_spec import RangeSpec
from axiestudio.helpers.data import safe_convert
from axiestudio.io import BoolInput, DropdownInput, IntInput, MessageTextInput, Output, SliderInput, TableInput
from axiestudio.schema.dataframe import DataFrame
from axiestudio.schema.message import Message
from axiestudio.services.deps import get_settings_service

# Constants
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_DEPTH = 1
DEFAULT_FORMAT = "Text"
URL_REGEX = re.compile(
    r"^(https?:\/\/)?" r"(www\.)?" r"([a-zA-Z0-9.-]+)" r"(\.[a-zA-Z]{2,})?" r"(:\d+)?" r"(\/[^\s]*)?$",
    re.IGNORECASE,
)


class URLComponent(Component):
    """En komponent som laddar och tolkar innehåll från webbsidor rekursivt.

    Denna komponent tillåter hämtning av innehåll från en eller flera URL:er, med alternativ att:
    - Kontrollera crawldjup
    - Förhindra crawling utanför rotdomänen
    - Använda asynkron laddning för bättre prestanda
    - Extrahera antingen rå HTML eller ren text
    - Konfigurera förfrågningsrubriker och timeouts
    """

    display_name = "URL"
    description = "Hämta innehåll från en eller flera webbsidor, följ länkar rekursivt."
    documentation: str = "https://docs.axiestudio.org/components-data#url"
    icon = "layout-template"
    name = "URLComponent"

    inputs = [
        MessageTextInput(
            name="urls",
            display_name="URLs",
            info="Ange en eller flera URL:er att crawla rekursivt, genom att klicka på '+'-knappen.",
            is_list=True,
            tool_mode=True,
            placeholder="Ange en URL...",
            list_add_label="Lägg till URL",
            input_types=[],
        ),
        SliderInput(
            name="max_depth",
            display_name="Djup",
            info=(
                "Styr hur många 'klick' bort från den initiala sidan crawlern kommer att gå:\n"
                "- djup 1: endast den initiala sidan\n"
                "- djup 2: initial sida + alla sidor länkade direkt från den\n"
                "- djup 3: initial sida + direkta länkar + länkar som finns på dessa direktlänkade sidor\n"
                "Obs: Detta handlar om länktraversering, inte URL-sökvägsdjup."
            ),
            value=DEFAULT_MAX_DEPTH,
            range_spec=RangeSpec(min=1, max=5, step=1),
            required=False,
            min_label=" ",
            max_label=" ",
            min_label_icon="None",
            max_label_icon="None",
            # slider_input=True
        ),
        BoolInput(
            name="prevent_outside",
            display_name="Förhindra utanför",
            info=(
                "Om aktiverat crawlar endast URL:er inom samma domän som rot-URL:en. "
                "Detta hjälper till att förhindra att crawlern går till externa webbplatser."
            ),
            value=True,
            required=False,
            advanced=True,
        ),
        BoolInput(
            name="use_async",
            display_name="Använd asynkron",
            info=(
                "Om aktiverat använder asynkron laddning som kan vara betydligt snabbare "
                "men kan använda mer systemresurser."
            ),
            value=True,
            required=False,
            advanced=True,
        ),
        DropdownInput(
            name="format",
            display_name="Utdataformat",
            info="Utdataformat. Använd 'Text' för att extrahera texten från HTML eller 'HTML' för rått HTML-innehåll.",
            options=["Text", "HTML"],
            value=DEFAULT_FORMAT,
            advanced=True,
        ),
        IntInput(
            name="timeout",
            display_name="Timeout",
            info="Timeout för förfrågan i sekunder.",
            value=DEFAULT_TIMEOUT,
            required=False,
            advanced=True,
        ),
        TableInput(
            name="headers",
            display_name="Rubriker",
            info="Rubrikerna att skicka med förfrågan",
            table_schema=[
                {
                    "name": "key",
                    "display_name": "Rubrik",
                    "type": "str",
                    "description": "Rubriknamn",
                },
                {
                    "name": "value",
                    "display_name": "Värde",
                    "type": "str",
                    "description": "Rubrikvärde",
                },
            ],
            value=[{"key": "User-Agent", "value": get_settings_service().settings.user_agent}],
            advanced=True,
            input_types=["DataFrame"],
        ),
        BoolInput(
            name="filter_text_html",
            display_name="Filtrera text/HTML",
            info="Om aktiverat filtreras text/css-innehållstyp bort från resultaten.",
            value=True,
            required=False,
            advanced=True,
        ),
        BoolInput(
            name="continue_on_failure",
            display_name="Fortsätt vid fel",
            info="Om aktiverat fortsätter crawling även om vissa förfrågningar misslyckas.",
            value=True,
            required=False,
            advanced=True,
        ),
        BoolInput(
            name="check_response_status",
            display_name="Kontrollera svarsstatus",
            info="Om aktiverat kontrolleras svarsstatusen för förfrågan.",
            value=False,
            required=False,
            advanced=True,
        ),
        BoolInput(
            name="autoset_encoding",
            display_name="Automatisk kodning",
            info="Om aktiverat ställs kodningen för förfrågan in automatiskt.",
            value=True,
            required=False,
            advanced=True,
        ),
    ]

    outputs = [
        Output(display_name="Extraherade sidor", name="page_results", method="fetch_content"),
        Output(display_name="Rått innehåll", name="raw_results", method="fetch_content_as_message", tool_mode=False),
    ]

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validates if the given string matches URL pattern.

        Args:
            url: The URL string to validate

        Returns:
            bool: True if the URL is valid, False otherwise
        """
        return bool(URL_REGEX.match(url))

    def ensure_url(self, url: str) -> str:
        """Ensures the given string is a valid URL.

        Args:
            url: The URL string to validate and normalize

        Returns:
            str: The normalized URL

        Raises:
            ValueError: If the URL is invalid
        """
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        if not self.validate_url(url):
            msg = f"Ogiltig URL: {url}"
            raise ValueError(msg)

        return url

    def _create_loader(self, url: str) -> RecursiveUrlLoader:
        """Creates a RecursiveUrlLoader instance with the configured settings.

        Args:
            url: The URL to load

        Returns:
            RecursiveUrlLoader: Configured loader instance
        """
        headers_dict = {header["key"]: header["value"] for header in self.headers}
        extractor = (lambda x: x) if self.format == "HTML" else (lambda x: BeautifulSoup(x, "lxml").get_text())

        return RecursiveUrlLoader(
            url=url,
            max_depth=self.max_depth,
            prevent_outside=self.prevent_outside,
            use_async=self.use_async,
            extractor=extractor,
            timeout=self.timeout,
            headers=headers_dict,
            check_response_status=self.check_response_status,
            continue_on_failure=self.continue_on_failure,
            base_url=url,  # Add base_url to ensure consistent domain crawling
            autoset_encoding=self.autoset_encoding,  # Enable automatic encoding detection
            exclude_dirs=[],  # Allow customization of excluded directories
            link_regex=None,  # Allow customization of link filtering
        )

    def fetch_url_contents(self) -> list[dict]:
        """Load documents from the configured URLs.

        Returns:
            List[Data]: List of Data objects containing the fetched content

        Raises:
            ValueError: If no valid URLs are provided or if there's an error loading documents
        """
        try:
            urls = list({self.ensure_url(url) for url in self.urls if url.strip()})
            logger.debug(f"URLs: {urls}")
            if not urls:
                msg = "Inga giltiga URL:er angivna."
                raise ValueError(msg)

            all_docs = []
            for url in urls:
                logger.debug(f"Loading documents from {url}")

                try:
                    loader = self._create_loader(url)
                    docs = loader.load()

                    if not docs:
                        logger.warning(f"No documents found for {url}")
                        continue

                    logger.debug(f"Found {len(docs)} documents from {url}")
                    all_docs.extend(docs)

                except requests.exceptions.RequestException as e:
                    logger.exception(f"Error loading documents from {url}: {e}")
                    continue

            if not all_docs:
                msg = "Inga dokument laddades framgångsrikt från någon URL"
                raise ValueError(msg)

            # data = [Data(text=doc.page_content, **doc.metadata) for doc in all_docs]
            data = [
                {
                    "text": safe_convert(doc.page_content, clean_data=True),
                    "url": doc.metadata.get("source", ""),
                    "title": doc.metadata.get("title", ""),
                    "description": doc.metadata.get("description", ""),
                    "content_type": doc.metadata.get("content_type", ""),
                    "language": doc.metadata.get("language", ""),
                }
                for doc in all_docs
            ]
        except Exception as e:
            error_msg = e.message if hasattr(e, "message") else e
            msg = f"Fel vid laddning av dokument: {error_msg!s}"
            logger.exception(msg)
            raise ValueError(msg) from e
        return data

    def fetch_content(self) -> DataFrame:
        """Convert the documents to a DataFrame."""
        return DataFrame(data=self.fetch_url_contents())

    def fetch_content_as_message(self) -> Message:
        """Convert the documents to a Message."""
        url_contents = self.fetch_url_contents()
        return Message(text="\n\n".join([x["text"] for x in url_contents]), data={"data": url_contents})
