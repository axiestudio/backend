from langchain_community.tools import DuckDuckGoSearchRun

from axiestudio.custom.custom_component.component import Component
from axiestudio.inputs.inputs import IntInput, MessageTextInput
from axiestudio.schema.data import Data
from axiestudio.schema.dataframe import DataFrame
from axiestudio.template.field.base import Output


class DuckDuckGoSearchComponent(Component):
    """Component for performing web searches using DuckDuckGo."""

    display_name = "DuckDuckGo-sökning"
    description = "Sök på webben med DuckDuckGo med anpassningsbara resultatgränser"
    documentation = "https://python.langchain.com/docs/integrations/tools/ddg"
    icon = "DuckDuckGo"

    inputs = [
        MessageTextInput(
            name="input_value",
            display_name="Sökfråga",
            required=True,
            info="Sökfrågan att utföra med DuckDuckGo",
            tool_mode=True,
        ),
        IntInput(
            name="max_results",
            display_name="Max resultat",
            value=5,
            required=False,
            advanced=True,
            info="Maximalt antal sökresultat att returnera",
        ),
        IntInput(
            name="max_snippet_length",
            display_name="Max utdragslängd",
            value=100,
            required=False,
            advanced=True,
            info="Maximal längd för varje resultatutdrag",
        ),
    ]

    outputs = [
        Output(display_name="DataFrame", name="dataframe", method="fetch_content_dataframe"),
    ]

    def _build_wrapper(self) -> DuckDuckGoSearchRun:
        """Build the DuckDuckGo search wrapper."""
        return DuckDuckGoSearchRun()

    def run_model(self) -> DataFrame:
        return self.fetch_content_dataframe()

    def fetch_content(self) -> list[Data]:
        """Execute the search and return results as Data objects."""
        try:
            wrapper = self._build_wrapper()

            full_results = wrapper.run(f"{self.input_value} (site:*)")

            result_list = full_results.split("\n")[: self.max_results]

            data_results = []
            for result in result_list:
                if result.strip():
                    snippet = result[: self.max_snippet_length]
                    data_results.append(
                        Data(
                            text=snippet,
                            data={
                                "content": result,
                                "snippet": snippet,
                            },
                        )
                    )
        except (ValueError, AttributeError) as e:
            error_data = [Data(text=str(e), data={"error": str(e)})]
            self.status = error_data
            return error_data
        else:
            self.status = data_results
            return data_results

    def fetch_content_dataframe(self) -> DataFrame:
        """Convert the search results to a DataFrame.

        Returns:
            DataFrame: A DataFrame containing the search results.
        """
        data = self.fetch_content()
        return DataFrame(data)
