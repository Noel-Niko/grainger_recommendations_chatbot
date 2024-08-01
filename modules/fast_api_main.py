import asyncio
import logging
from typing import Dict, List

import httpx
from fastapi import FastAPI

from modules.rest_modules.endpoints import chat, health, image, review
from modules.vector_index.vector_implimentations import initialize_embeddings_and_faiss

logging.basicConfig(level=logging.INFO)
app = FastAPI()

session_store: Dict[str, List[Dict[str, str]]] = {}
current_tasks: Dict[str, asyncio.Task] = {}


class MainResourceManager:
    def __init__(self):
        self.bedrock_embeddings, self.vectorstore_faiss_doc, self.df, self.llm = initialize_embeddings_and_faiss()
        self.driver = None
        self.http_client = None
        self.initialize_http_client()

    def initialize_http_client(self):
        try:
            self.http_client = httpx.AsyncClient(limits=httpx.Limits(max_connections=200, max_keepalive_connections=50))
            logging.info("HTTP client initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize HTTP client: {e}")

    async def refresh_bedrock_embeddings(self):
        self.bedrock_embeddings, self.vectorstore_faiss_doc, self.df, self.llm = initialize_embeddings_and_faiss()


resource_manager = MainResourceManager()


@app.on_event("startup")
async def startup_event():
    logging.info("Startup complete.")
    global session_store, current_tasks
    session_store = {}
    current_tasks = {}
    resource_manager.initialize_http_client()


@app.on_event("shutdown")
async def shutdown_event():
    if resource_manager.driver:
        resource_manager.driver.quit()
    await resource_manager.http_client.aclose()
    logging.info("Shutdown complete.")


app.include_router(chat.router)
app.include_router(image.router)
app.include_router(review.router)
app.include_router(health.router)

if __name__ == "__main__":
    import uvicorn

    port = 8000
    uvicorn.run(app, host="0.0.0.0", port=port)

#
#
#
# import asyncio
# import base64
# import io
# import logging
# import traceback
# from asyncio import Semaphore
# from typing import Dict, List
#
# import httpx
# import selenium
# from fastapi import Depends, FastAPI, HTTPException, Request
# from fastapi.responses import JSONResponse
# from PIL import Image
# from pydantic import BaseModel
#
# from modules.rest_modules.rest_utils.image_utils.grainger_image_util import get_images
# from modules.vector_index.vector_utils.chat_processor import (
#     process_chat_question_with_customer_attribute_identifier,
# )
# from modules.vector_index.document import initialize_embeddings_and_faiss
# from modules.web_extraction_tools.product_reviews.call_selenium_for_review_async import (
#     async_navigate_to_reviews_selenium,
# )
#
# tag = "fast_api_main"
# app = FastAPI()
#
# session_store: Dict[str, List[Dict[str, str]]] = {}
# current_tasks: Dict[str, asyncio.Task] = {}
#
# logging.basicConfig(level=logging.INFO)
#
#
# class ResourceManager:
#     def __init__(self):
#         self.bedrock_embeddings, self.vectorstore_faiss_doc, self.df, self.llm = initialize_embeddings_and_faiss()
#         self.driver = None
#         self.http_client = None
#         self.initialize_http_client()
#
#     def initialize_http_client(self):
#         try:
#             self.http_client = httpx.AsyncClient(limits=httpx.Limits(max_connections=200, max_keepalive_connections=50))
#             logging.info("HTTP client initialized successfully.")
#         except Exception as e:
#             logging.error(f"Failed to initialize HTTP client: {e}")
#
#     async def refresh_bedrock_embeddings(self):
#         self.bedrock_embeddings, self.vectorstore_faiss_doc, self.df, self.llm = initialize_embeddings_and_faiss()
#
#
# resource_manager = ResourceManager()
#
#
# @app.on_event("shutdown")
# async def shutdown_event():
#     if resource_manager.driver:
#         resource_manager.driver.quit()
#     await resource_manager.http_client.aclose()
#     logging.info("Shutdown complete.")
#
#
# @app.on_event("startup")
# async def startup_event():
#     logging.info("Startup complete.")
#     global session_store, current_tasks
#     session_store = {}
#     current_tasks = {}
#
#
# class ChatRequest(BaseModel):
#     question: str
#     clear_history: bool = False
#
#
# async def get_resource_manager():
#     return resource_manager
#
# resource_manager_dependency = Depends(get_resource_manager)
#
# @app.post("/ask_question")
# async def ask_question(
#         chat_request: ChatRequest,
#         request: Request,
#         resource_manager_param: ResourceManager = resource_manager_dependency
# ):
#     try:
#         session_id = request.headers.get("session-id")
#         if not session_id:
#             raise HTTPException(status_code=400, detail="Session ID is required")
#
#         if session_id not in session_store:
#             session_store[session_id] = []
#             logging.info(f"{tag}/ Adding new session ID {session_id} to session_store")
#
#         logging.info(f"{tag}/ Received question: {chat_request.question} with session_id: {session_id}")
#
#         # Cancel ongoing tasks if present for the same session ID
#         if session_id in current_tasks and not current_tasks[session_id].done():
#             logging.info(f"Cancelling task for session ID: {session_id} due to new question.")
#             current_tasks[session_id].cancel()
#             await current_tasks[session_id]
#
#         task = asyncio.create_task(process_question_task(chat_request, session_id, resource_manager_param))
#         current_tasks[session_id] = task
#
#         response = await task
#
#         return response
#
#     except Exception as e:
#         logging.error(f"Error in {tag}/ask_question: {str(e)}")
#         logging.error(traceback.format_exc())
#         raise HTTPException(status_code=500, detail="Internal Server Error")
#
#
# async def process_question_task(chat_request, session_id, resource_manager_param):
#     try:
#         message, response_json, customer_attributes_retrieved, time_to_get_attributes = await process_chat_question(
#             chat_request.question, chat_request.clear_history, session_id, resource_manager_param
#         )
#
#         if response_json is None:
#             logging.error(f"{tag}/ Response json is None")
#             raise HTTPException(status_code=500, detail=f"{tag}/ Error processing chat question, response is None")
#
#         products = response_json.get('products', [])
#         logging.info(f"{tag}/ Products retrieved: {products}")
#
#         # Update the session history with the latest question and response
#         session_store[session_id].append({
#             "question": chat_request.question,
#             "response": response_json
#         })
#
#         return {
#             "message": message,
#             "customer_attributes_retrieved": customer_attributes_retrieved,
#             "time_to_get_attributes": time_to_get_attributes,
#             "products": products
#         }
#     except asyncio.CancelledError:
#         logging.info(f"{tag}/ Task for session_id {session_id} was cancelled due to new question.")
#         return {
#             "message": "Task cancelled due to new question",
#             "products": []
#         }
#     except Exception as e:
#         logging.error(f"Error in {tag}/process_question_task: {str(e)}")
#         logging.error(traceback.format_exc())
#         raise HTTPException(status_code=500, detail="Internal Server Error")
#
#
# async def process_chat_question(question, clear_history, session_id, resource_manager_param):
#     try:
#         if clear_history:
#             logging.info(f"{tag}/ Clearing chat history for session_id: {session_id}")
#             session_store[session_id] = []
#
#         chat_history = session_store.get(session_id, [])
#         logging.info(f"{tag}/ Current chat history for session_id {session_id}: {chat_history}")
#
#         logging.info(f"{tag}/ Processing question: {question}")
#         message, response_json, customer_attributes_retrieved, time_to_get_attributes = process_chat_question_with_customer_attribute_identifier(
#             question,
#             resource_manager_param.vectorstore_faiss_doc,
#             resource_manager_param.llm,
#             chat_history
#         )
#
#         chat_history.append(
#             f"QUESTION: {question}. MESSAGE: {message}. CUSTOMER ATTRIBUTES: {customer_attributes_retrieved}")
#         session_store[session_id] = chat_history
#
#         return message, response_json, customer_attributes_retrieved, time_to_get_attributes
#     except Exception as e:
#         logging.error(f"{tag}/ Error processing chat question: {str(e)}")
#         logging.error(traceback.format_exc())
#         raise
#
#
# @app.post("/fetch_images")
# async def fetch_images(request: Request, resource_manager_param: ResourceManager = Depends(get_resource_manager)):
#     try:
#         products = await request.json()
#         recommendations_list = [f"{product['product']}, {product['code']}" for product in products]
#         logging.info(f"{tag}/ Fetching images for products: {recommendations_list}")
#         image_data, total_image_time = await get_images(recommendations_list, resource_manager_param.df)
#         logging.info(f"{tag}/ Total time to fetch images: {total_image_time} seconds." '\n'"Image data: {image_data}")
#
#         image_responses = []
#         for image_info in image_data:
#             try:
#                 img = Image.open(io.BytesIO(image_info["Image Data"]))
#                 img_byte_arr = io.BytesIO()
#                 img.save(img_byte_arr, format='PNG')
#                 img_byte_arr = img_byte_arr.getvalue()
#                 encoded_image = base64.b64encode(img_byte_arr).decode('utf-8')
#                 image_responses.append({
#                     "code": image_info["Code"],
#                     "image_data": encoded_image
#                 })
#             except Exception as e:
#                 logging.error(f"Error processing image: {e}")
#         return image_responses
#     except Exception as e:
#         logging.error(f"Error fetching images: {e}")
#         logging.error(traceback.format_exc())
#         raise HTTPException(status_code=500, detail="Error fetching images")
#
#
# @app.post("/fetch_reviews")
# async def fetch_reviews(request: Request):
#     logging.info(f"{tag}/ Received request to fetch reviews.")
#     try:
#         products = await request.json()
#         logging.info(f"{tag}/ Received products for review fetching: {products}")
#
#         review_tasks = [fetch_review_for_product(product) for product in products]
#         reviews = await asyncio.gather(*review_tasks)
#         reviews = [review for review in reviews if review is not None]
#
#         logging.info(f"{tag}/ Completed review fetching for all products.")
#         return {"status": "completed", "reviews": reviews}
#     except Exception as e:
#         logging.error(f"{tag}/ Error fetching reviews: {e}")
#         logging.error(traceback.format_exc())
#         raise HTTPException(status_code=500, detail="Error fetching reviews")
#
#
# async def fetch_review_for_product(product):
#     semaphore = Semaphore(10)
#     async with semaphore:
#         product_info = f"{product['product']}, {product['code']}"
#         logging.info(f"{tag}/ Fetching reviews for product: {product_info}")
#
#         try:
#             reviews_data = await async_navigate_to_reviews_selenium(product_info)
#         except selenium.common.exceptions.TimeoutException as e:
#             logging.error(f"{tag}/ TimeoutException navigating to reviews for {product_info}: {str(e)}")
#             return None
#         except selenium.common.exceptions.NoSuchElementException as e:
#             logging.error(f"{tag}/ NoSuchElementError navigating to reviews for {product_info}: {str(e)}")
#             return None
#         except Exception as e:
#             logging.error(f"{tag}/ Error navigating to reviews for {product_info}: {str(e)}")
#             logging.error(f"Stacktrace: {traceback.format_exc()}")
#             return None
#
#         if reviews_data:
#             review = {
#                 "code": product['code'],
#                 "average_star_rating": reviews_data['Average Star Rating'],
#                 "average_recommendation_percent": reviews_data['Average Recommendation Percent'],
#                 "review_texts": reviews_data['Review Texts']
#             }
#             logging.info(f"{tag}/ Reviews for product {product['code']}: {reviews_data}")
#             return review
#         else:
#             logging.info(f"{tag}/ No reviews found for product {product['code']}")
#             return None
#
#
# # Health check endpoint
# @app.get("/health")
# async def health_check():
#     return JSONResponse(content={"status": "healthy"})
#
#
# @app.get("/")
# async def read_root():
#     return {"message": "Welcome to the Grainger Recommendations API"}
#
#
# @app.get("/favicon.ico")
# async def favicon():
#     return JSONResponse(content={"message": "No favicon available"}, status_code=204)
#
#
# if __name__ == "__main__":
#     import uvicorn
#
#     port = 8000
#     uvicorn.run(app, host="0.0.0.0", port=port)
