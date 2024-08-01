from modules.vector_index.vector_facades.DocumentFacade import DocumentFacade


class DocumentImpl(DocumentFacade):
    def __init__(self, page_content, metadata):
        super().__init__()
        self.page_content = page_content
        self.metadata = metadata