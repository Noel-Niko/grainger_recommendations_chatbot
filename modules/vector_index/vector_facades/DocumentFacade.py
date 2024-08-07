# import abc
# from abc import ABC
#
#
# class Document:
#     def __init__(self, page_content, metadata):
#         self.page_content = page_content
#         self.metadata = metadata
#
# class DocumentFacade(ABC):
#     def __init__(self):
#         pass
#
#     @abc.abstractmethod
#     def initialize_embeddings_and_faiss(self):
#         pass
#
#     @abc.abstractmethod
#     def parallel_search(self, queries, vectorstore_faiss_doc, k=5, search_type="similarity", num_threads=5):
#         pass
