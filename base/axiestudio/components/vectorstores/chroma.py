from copy import deepcopy
from typing import TYPE_CHECKING

from chromadb.config import Settings
from langchain_chroma import Chroma
from typing_extensions import override

from axiestudio.base.vectorstores.model import LCVectorStoreComponent, check_cached_vector_store
from axiestudio.base.vectorstores.utils import chroma_collection_to_data
from axiestudio.inputs.inputs import BoolInput, DropdownInput, HandleInput, IntInput, StrInput
from axiestudio.schema.data import Data

if TYPE_CHECKING:
    from axiestudio.schema.dataframe import DataFrame


class ChromaVectorStoreComponent(LCVectorStoreComponent):
    """Chroma Vektorlager med sökmöjligheter."""

    display_name: str = "Chroma DB"
    description: str = "Chroma Vector Store med sökmöjligheter"
    name = "Chroma"
    icon = "Chroma"

    inputs = [
        StrInput(
            name="collection_name",
            display_name="Samlingsnamn",
            value="axiestudio",
        ),
        StrInput(
            name="persist_directory",
            display_name="Beständig katalog",
        ),
        *LCVectorStoreComponent.inputs,
        HandleInput(name="embedding", display_name="Inbäddning", input_types=["Embeddings"]),
        StrInput(
            name="chroma_server_cors_allow_origins",
            display_name="Server CORS tillåtna ursprung",
            advanced=True,
        ),
        StrInput(
            name="chroma_server_host",
            display_name="Servervärd",
            advanced=True,
        ),
        IntInput(
            name="chroma_server_http_port",
            display_name="Server HTTP-port",
            advanced=True,
        ),
        IntInput(
            name="chroma_server_grpc_port",
            display_name="Server gRPC-port",
            advanced=True,
        ),
        BoolInput(
            name="chroma_server_ssl_enabled",
            display_name="Server SSL aktiverat",
            advanced=True,
        ),
        BoolInput(
            name="allow_duplicates",
            display_name="Tillåt dubbletter",
            advanced=True,
            info="Om falskt kommer dokument som redan finns i Vector Store inte att läggas till.",
        ),
        DropdownInput(
            name="search_type",
            display_name="Söktyp",
            options=["Similarity", "MMR"],
            value="Similarity",
            advanced=True,
        ),
        IntInput(
            name="number_of_results",
            display_name="Antal resultat",
            info="Antal resultat att returnera.",
            advanced=True,
            value=10,
        ),
        IntInput(
            name="limit",
            display_name="Gräns",
            advanced=True,
            info="Begränsa antalet poster att jämföra när Tillåt dubbletter är falskt.",
        ),
    ]

    @override
    @check_cached_vector_store
    def build_vector_store(self) -> Chroma:
        """Builds the Chroma object."""
        try:
            from chromadb import Client
            from langchain_chroma import Chroma
        except ImportError as e:
            msg = "Kunde inte importera Chroma-integrationspaketet. Vänligen installera det med `pip install langchain-chroma`."
            raise ImportError(msg) from e
        # Chroma settings
        chroma_settings = None
        client = None
        if self.chroma_server_host:
            chroma_settings = Settings(
                chroma_server_cors_allow_origins=self.chroma_server_cors_allow_origins or [],
                chroma_server_host=self.chroma_server_host,
                chroma_server_http_port=self.chroma_server_http_port or None,
                chroma_server_grpc_port=self.chroma_server_grpc_port or None,
                chroma_server_ssl_enabled=self.chroma_server_ssl_enabled,
            )
            client = Client(settings=chroma_settings)

        # Check persist_directory and expand it if it is a relative path
        persist_directory = self.resolve_path(self.persist_directory) if self.persist_directory is not None else None

        chroma = Chroma(
            persist_directory=persist_directory,
            client=client,
            embedding_function=self.embedding,
            collection_name=self.collection_name,
        )

        self._add_documents_to_vector_store(chroma)
        self.status = chroma_collection_to_data(chroma.get(limit=self.limit))
        return chroma

    def _add_documents_to_vector_store(self, vector_store: "Chroma") -> None:
        """Adds documents to the Vector Store."""
        ingest_data: list | Data | DataFrame = self.ingest_data
        if not ingest_data:
            self.status = ""
            return

        # Convert DataFrame to Data if needed using parent's method
        ingest_data = self._prepare_ingest_data()

        stored_documents_without_id = []
        if self.allow_duplicates:
            stored_data = []
        else:
            stored_data = chroma_collection_to_data(vector_store.get(limit=self.limit))
            for value in deepcopy(stored_data):
                del value.id
                stored_documents_without_id.append(value)

        documents = []
        for _input in ingest_data or []:
            if isinstance(_input, Data):
                if _input not in stored_documents_without_id:
                    documents.append(_input.to_lc_document())
            else:
                msg = "Vektorlager-indata måste vara Data-objekt."
                raise TypeError(msg)

        if documents and self.embedding is not None:
            self.log(f"Lägger till {len(documents)} dokument i Vektorlagret.")
            vector_store.add_documents(documents)
        else:
            self.log("Inga dokument att lägga till i Vektorlagret.")
