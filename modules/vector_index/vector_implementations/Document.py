

class Document:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata

# class DocumentImpl(DocumentFacade):
#     # def __init__(self, page_content, metadata):
#     #     super().__init__()
#     #     self.page_content = page_content
#     #     self.metadata = metadata
#
#     def initialize_embeddings_and_faiss(self):
#         pass
#
#     def parallel_search(self, queries, vectorstore_faiss_doc, k=5, search_type="similarity", num_threads=5):
#         pass
