import logging
import httpx
from modules.vector_index.document import initialize_embeddings_and_faiss

class ResourceManager:
    def __init__(self):
        self.bedrock_embeddings, self.vectorstore_faiss_doc, self.df, self.llm = initialize_embeddings_and_faiss()
        self.driver = None
        self.http_client = None

    async def initialize_http_client(self):
        try:
            self.http_client = httpx.AsyncClient(limits=httpx.Limits(max_connections=200, max_keepalive_connections=50))
            logging.info("HTTP client initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize HTTP client: {e}")

    async def refresh_bedrock_embeddings(self):
        self.bedrock_embeddings, self.vectorstore_faiss_doc, self.df, self.llm = initialize_embeddings_and_faiss()

resource_manager = ResourceManager()
