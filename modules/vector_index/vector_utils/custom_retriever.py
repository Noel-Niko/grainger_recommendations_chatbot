import logging
import sys
from typing import Any, List

from langchain_core.callbacks.manager import (
    AsyncCallbackManagerForRetrieverRun,
    CallbackManagerForRetrieverRun,
)
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import run_in_executor
from pydantic import Field

tag = "custom_retriever"
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

class CustomRetriever(BaseRetriever):
    vectorstore_impl: Any
    k: int = Field(default=6)

    def __init__(self, vectorstore_impl: Any, k: int = 6, **data: Any):
        super().__init__(**data)
        self.vectorstore_impl = vectorstore_impl
        self.k = k

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        results = self.vectorstore_impl.parallel_search([query], k=self.k)
        if results is not None and results[0] is not None:
            logging.info(f"{tag} / Retrieved {len(results[0])} documents: {results[0]}")
        return results[0]

    async def _aget_relevant_documents(
        self, query: str, *, run_manager: AsyncCallbackManagerForRetrieverRun
    ) -> List[Document]:
        return await run_in_executor(
            None,
            self._get_relevant_documents,
            query,
            run_manager=run_manager.get_sync(),
        )
