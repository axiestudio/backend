from typing import cast

from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper

from axiestudio.base.langchain_utilities.model import LCToolComponent
from axiestudio.field_typing import Tool
from axiestudio.inputs.inputs import BoolInput, IntInput, MessageTextInput, MultilineInput
from axiestudio.schema.data import Data


class WikipediaAPIComponent(LCToolComponent):
    display_name = "Wikipedia API [Föråldrad]"
    description = "Anropa Wikipedia API."
    name = "WikipediaAPI"
    icon = "Wikipedia"
    legacy = True

    inputs = [
        MultilineInput(
            name="input_value",
            display_name="Inmatning",
        ),
        MessageTextInput(name="lang", display_name="Språk", value="en"),
        IntInput(name="k", display_name="Antal resultat", value=4, required=True),
        BoolInput(name="load_all_available_meta", display_name="Ladda all tillgänglig metadata", value=False, advanced=True),
        IntInput(
            name="doc_content_chars_max", display_name="Max tecken för dokumentinnehåll", value=4000, advanced=True
        ),
    ]

    def run_model(self) -> list[Data]:
        wrapper = self._build_wrapper()
        docs = wrapper.load(self.input_value)
        data = [Data.from_document(doc) for doc in docs]
        self.status = data
        return data

    def build_tool(self) -> Tool:
        wrapper = self._build_wrapper()
        return cast("Tool", WikipediaQueryRun(api_wrapper=wrapper))

    def _build_wrapper(self) -> WikipediaAPIWrapper:
        return WikipediaAPIWrapper(
            top_k_results=self.k,
            lang=self.lang,
            load_all_available_meta=self.load_all_available_meta,
            doc_content_chars_max=self.doc_content_chars_max,
        )
