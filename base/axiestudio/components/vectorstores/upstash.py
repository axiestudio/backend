from langchain_community.vectorstores import UpstashVectorStore

from axiestudio.base.vectorstores.model import LCVectorStoreComponent, check_cached_vector_store
from axiestudio.helpers.data import docs_to_data
from axiestudio.io import (
    HandleInput,
    IntInput,
    MultilineInput,
    SecretStrInput,
    StrInput,
)
from axiestudio.schema.data import Data


class UpstashVectorStoreComponent(LCVectorStoreComponent):
    display_name = "Upstash"
    description = "Upstash Vektorlager med sökmöjligheter"
    name = "Upstash"
    icon = "Upstash"

    inputs = [
        StrInput(
            name="index_url",
            display_name="Index-URL",
            info="URL:en för Upstash-indexet.",
            required=True,
        ),
        SecretStrInput(
            name="index_token",
            display_name="Index-token",
            info="Token för Upstash-indexet.",
            required=True,
        ),
        StrInput(
            name="text_key",
            display_name="Textnyckel",
            info="Nyckeln i posten att använda som text.",
            value="text",
            advanced=True,
        ),
        StrInput(
            name="namespace",
            display_name="Namnrymd",
            info="Lämna tom för standardnamnrymd.",
        ),
        *LCVectorStoreComponent.inputs,
        MultilineInput(
            name="metadata_filter",
            display_name="Metadatafilter",
            info="Filtrerar dokument efter metadata. Se dokumentationen för mer information.",
        ),
        HandleInput(
            name="embedding",
            display_name="Inbäddning",
            input_types=["Embeddings"],
            info="För att använda Upstashs inbäddningar, ange ingen inbäddning.",
        ),
        IntInput(
            name="number_of_results",
            display_name="Antal resultat",
            info="Antal resultat att returnera.",
            value=4,
            advanced=True,
        ),
    ]

    @check_cached_vector_store
    def build_vector_store(self) -> UpstashVectorStore:
        use_upstash_embedding = self.embedding is None

        # Convert DataFrame to Data if needed using parent's method
        self.ingest_data = self._prepare_ingest_data()

        documents = []
        for _input in self.ingest_data or []:
            if isinstance(_input, Data):
                documents.append(_input.to_lc_document())
            else:
                documents.append(_input)

        if documents:
            if use_upstash_embedding:
                upstash_vs = UpstashVectorStore(
                    embedding=use_upstash_embedding,
                    text_key=self.text_key,
                    index_url=self.index_url,
                    index_token=self.index_token,
                    namespace=self.namespace,
                )
                upstash_vs.add_documents(documents)
            else:
                upstash_vs = UpstashVectorStore.from_documents(
                    documents=documents,
                    embedding=self.embedding,
                    text_key=self.text_key,
                    index_url=self.index_url,
                    index_token=self.index_token,
                    namespace=self.namespace,
                )
        else:
            upstash_vs = UpstashVectorStore(
                embedding=self.embedding or use_upstash_embedding,
                text_key=self.text_key,
                index_url=self.index_url,
                index_token=self.index_token,
                namespace=self.namespace,
            )

        return upstash_vs

    def search_documents(self) -> list[Data]:
        vector_store = self.build_vector_store()

        if self.search_query and isinstance(self.search_query, str) and self.search_query.strip():
            docs = vector_store.similarity_search(
                query=self.search_query,
                k=self.number_of_results,
                filter=self.metadata_filter,
            )

            data = docs_to_data(docs)
            self.status = data
            return data
        return []
