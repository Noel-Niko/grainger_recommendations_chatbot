import pickle
from modules.vector_index.vector_facades.DocumentFacade import DocumentFacade


class VectorStoreFacade(DocumentFacade):
    def __init__(self, vectorstore_faiss_doc):
        super().__init__()

    def initialize_embeddings_and_faiss(self,):
        pass

    def parallel_search(self, queries, vectorstore_faiss_doc, k=5, search_type="similarity", num_threads=5):
        pass
