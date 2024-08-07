import asyncio
import logging
import threading
from typing import Dict, List

import httpx
from fastapi import FastAPI

from modules.rest_modules.endpoints import chat, health, image, review
from modules.vector_index.vector_implementations.VectorStoreImpl import VectorStoreImpl

faiss_creation_event = threading.Event()
logging.basicConfig(level=logging.INFO)
app = FastAPI()

session_store: Dict[str, List[Dict[str, str]]] = {}
current_tasks: Dict[str, asyncio.Task] = {}
tag = "fast_api_main"

class MainResourceManager:
    def __init__(self):
        try:
            logging.info(f"{tag} / Initializing MainResourceManager...")
            self.bedrock_embeddings, self.vectorstore_faiss_doc, self.exact_match_map, self.df, self.llm = VectorStoreImpl.initialize_embeddings_and_faiss()
            self.driver = None
            self.http_client = None
            self.initialize_http_client()
            logging.info(f"{tag} / MainResourceManager initialized successfully.")
        except Exception as e:
            logging.error(f"{tag} / Failed to initialize MainResourceManager: {e}")
            raise

    def initialize_http_client(self):
        try:
            self.http_client = httpx.AsyncClient(limits=httpx.Limits(max_connections=200, max_keepalive_connections=50))
            logging.info(f"{tag} / HTTP client initialized successfully.")
        except Exception as e:
            logging.error(f"{tag} / Failed to initialize HTTP client: {e}")

    async def refresh_bedrock_embeddings(self):
        try:
            self.bedrock_embeddings, self.vectorstore_faiss_doc, self.exact_match_map, self.df, self.llm = VectorStoreImpl.initialize_embeddings_and_faiss()
            logging.info(f"{tag} / Bedrock embeddings refreshed successfully.")
        except Exception as e:
            logging.error(f"{tag} / Failed to refresh Bedrock embeddings: {e}")


resource_manager = MainResourceManager()


@app.on_event("startup")
async def startup_event():
    try:
        faiss_creation_event.wait()
        logging.info(f"{tag} / Startup complete.")
        global session_store, current_tasks
        session_store = {}
        current_tasks = {}
        resource_manager.initialize_http_client()
    except Exception as e:
        logging.error(f"{tag} / Error during startup: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    try:
        if resource_manager.driver:
            resource_manager.driver.quit()
        await resource_manager.http_client.aclose()
        logging.info(f"{tag} / Shutdown complete.")
    except Exception as e:
        logging.error(f"{tag} / Error during shutdown: {e}")


app.include_router(chat.router)
app.include_router(image.router)
app.include_router(review.router)
app.include_router(health.router)

if __name__ == "__main__":
    import uvicorn

    try:
        port = 8000
        uvicorn.run(app, host="0.0.0.0", port=port)
    except Exception as e:
        logging.error(f"{tag} / Failed to start FastAPI server: {e}")
