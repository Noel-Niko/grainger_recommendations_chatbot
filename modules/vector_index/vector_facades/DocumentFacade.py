import abc
from abc import ABC


class DocumentFacade(ABC):
    def __init__(self):
        pass

    @abc.abstractmethod
    def initialize_embeddings_and_faiss(self):
        pass

    @abc.abstractmethod
    def parallel_search(self, queries, vectorstore_faiss_doc, k=5, search_type="similarity", num_threads=5):
        pass
