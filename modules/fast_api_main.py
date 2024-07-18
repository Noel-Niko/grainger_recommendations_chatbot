import asyncio
import logging
import json
import time
import traceback
import uuid

from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException, Request, Depends, WebSocket
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from selenium.common import WebDriverException
from modules.image_utils.grainger_image_util import get_images
from modules.vector_index.chat_processor import process_chat_question_with_customer_attribute_identifier
from modules.vector_index.document import initialize_embeddings_and_faiss
from modules.web_extraction_tools.product_reviews.call_selenium_for_review_async import async_navigate_to_reviews_selenium
import base64
import io
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from starlette.websockets import WebSocketDisconnect
import httpx

tag = "fast_api_main"
app = FastAPI()

session_store = {}

logging.basicConfig(level=logging.INFO)

class ResourceManager:
    def __init__(self):
        self.bedrock_embeddings, self.vectorstore_faiss_doc, self.df, self.llm = initialize_embeddings_and_faiss()
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        try:
            logging.info("Initializing ChromeDriver...")
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            logging.info("ChromeDriver initialized successfully.")
        except WebDriverException as e:
            logging.error(f"WebDriver failed to start: {e}")
            self.driver = None

        self.http_client = httpx.AsyncClient(limits=httpx.Limits(max_connections=20, max_keepalive_connections=15))

    async def refresh_bedrock_embeddings(self):
        self.bedrock_embeddings, self.vectorstore_faiss_doc, self.df, self.llm = initialize_embeddings_and_faiss()

resource_manager = ResourceManager()

@app.on_event("startup")
async def startup_event():
    logging.info("Startup complete.")

@app.on_event("shutdown")
async def shutdown_event():
    if resource_manager.driver:
        resource_manager.driver.quit()
    await resource_manager.http_client.aclose()
    logging.info("Shutdown complete.")

class ChatRequest(BaseModel):
    question: str
    clear_history: bool = False

async def get_resource_manager():
    return resource_manager

@app.post("/ask_question")
async def ask_question(
        chat_request: ChatRequest,
        request: Request,
        resource_manager: ResourceManager = Depends(get_resource_manager)
):
    try:
        session_id = request.headers.get("session-id")
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID is required")

        if session_id not in session_store:
            session_store[session_id] = []  # Initialize as an empty list
            logging.info(f" {tag}/ Adding new session ID {session_id} to session_store")

        logging.info(f"{tag}/ Received question: {chat_request.question} with session_id: {session_id}")

        try:
            message, response_json, customer_attributes_retrieved, time_to_get_attributes = await process_chat_question(
                chat_request.question, chat_request.clear_history, session_id, resource_manager
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ExpiredTokenException':
                logging.info(f" {tag}/ Bedrock session expired, renewing...")
                await resource_manager.refresh_bedrock_embeddings()
                message, response_json, customer_attributes_retrieved, time_to_get_attributes = await process_chat_question(
                    chat_request.question, chat_request.clear_history, session_id, resource_manager
                )
            else:
                logging.error(f" {tag}/ Error: {str(e)}")
                raise e

        if response_json is None:
            logging.error(f"{tag}/ Response json is None")
            raise HTTPException(status_code=500, detail=f"{tag}/ Error processing chat question, response is None")

        products = response_json.get('products', [])
        logging.info(f"{tag}/ Products retrieved: {products}")

        return {
            "message": message,
            "customer_attributes_retrieved": customer_attributes_retrieved,
            "time_to_get_attributes": time_to_get_attributes,
            "products": products
        }

    except Exception as e:
        logging.error(f"Error in {tag}/ask_question: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def process_chat_question(question, clear_history, session_id, resource_manager):
    try:
        if clear_history:
            logging.info(f"{tag}/ Clearing chat history for session_id: {session_id}")
            session_store[session_id] = []

        chat_history = session_store.get(session_id, [])
        # logging.info(f"{tag}/ Current chat history for session_id {session_id}: {chat_history}")

        logging.info(f"{tag}/ Processing question: {question}")
        message, response_json, customer_attributes_retrieved, time_to_get_attributes = process_chat_question_with_customer_attribute_identifier(
            question,
            resource_manager.vectorstore_faiss_doc,
            resource_manager.llm,
            chat_history
        )
        # logging.info(f"{tag}/ Message: {message}")
        # logging.info(f"{tag}/ Response json: {response_json}")
        # logging.info(f"{tag}/ Customer attributes retrieved: {customer_attributes_retrieved}")
        # logging.info(f"{tag}/ Time to get attributes: {time_to_get_attributes}")

        chat_history.append(
            f"QUESTION: {question}. MESSAGE: {message}. CUSTOMER ATTRIBUTES: {customer_attributes_retrieved}")
        session_store[session_id] = chat_history

        # logging.info(f"{tag}/ Updated chat history for session_id {session_id}: {session_store[session_id]}")
        # logging.info(f"{tag}/ Processed question: {question} with message: {message}")

        return message, response_json, customer_attributes_retrieved, time_to_get_attributes
    except Exception as e:
        logging.error(f"{tag}/ Error processing chat question: {str(e)}")
        logging.error(traceback.format_exc())
        raise

@app.post("/fetch_images")
async def fetch_images(request: Request, resource_manager: ResourceManager = Depends(get_resource_manager)):
    try:
        products = await request.json()
        recommendations_list = [f"{product['product']}, {product['code']}" for product in products]
        logging.info(f"{tag}/ Fetching images for products: {recommendations_list}")
        image_data, total_image_time = await get_images(recommendations_list, resource_manager.df)
        logging.info(f"{tag}/ Total time to fetch images: {total_image_time} seconds." '\n'"Image data: {image_data}")

        image_responses = []
        for image_info in image_data:
            try:
                img = Image.open(io.BytesIO(image_info["Image Data"]))
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                encoded_image = base64.b64encode(img_byte_arr).decode('utf-8')
                image_responses.append({
                    "code": image_info["Code"],
                    "image_data": encoded_image
                })
            except Exception as e:
                logging.error(f"Error processing image: {e}")
        return image_responses
    except Exception as e:
        logging.error(f"Error fetching images: {e}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error fetching images")

@app.post("/fetch_reviews")
async def fetch_reviews(request: Request, resource_manager: ResourceManager = Depends(get_resource_manager)):
    logging.info(f"{tag}/ Received request to fetch reviews.")
    try:
        products = await request.json()
        logging.info(f"{tag}/ Received products for review fetching: {products}")

        review_tasks = [fetch_review_for_product(product, resource_manager) for product in products]
        reviews = await asyncio.gather(*review_tasks)
        reviews = [review for review in reviews if review is not None]

        logging.info(f"{tag}/ Completed review fetching for all products.")
        return {"status": "Reviews processing started", "reviews": reviews}
    except Exception as e:
        logging.error(f"{tag}/ Error fetching reviews: {e}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error fetching reviews")

async def fetch_review_for_product(product, resource_manager):
    product_info = f"{product['product']}, {product['code']}"
    logging.info(f"{tag}/ Fetching reviews for product: {product_info}")

    if resource_manager.driver:
        try:
            reviews_data = await async_navigate_to_reviews_selenium(product_info, resource_manager.driver)
        except Exception as e:
            logging.error(f"{tag}/ Error navigating to reviews for {product_info}: {str(e)}")
            return None

        if reviews_data:
            review = {
                "code": product['code'],
                "average_star_rating": reviews_data['Average Star Rating'],
                "average_recommendation_percent": reviews_data['Average Recommendation Percent'],
                "review_texts": reviews_data['Review Texts']
            }
            logging.info(f"{tag}/ Reviews for product {product['code']}: {reviews_data}")
            return review
        else:
            logging.info(f"{tag}/ No reviews found for product {product['code']}")
            return None
    else:
        logging.error(f"{tag}/ WebDriver is not initialized for product {product['code']}")
        return None


@app.websocket("/ws/reviews")
async def websocket_endpoint(websocket: WebSocket):
    logging.info(f"{tag}/ Starting reviews at {time.time()}")
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            products = json.loads(data)

            review_tasks = [fetch_review_for_product(product, resource_manager) for product in products]

            # Iterate over completed tasks and send each review to the client immediately
            for review_task in asyncio.as_completed(review_tasks):
                logging.info(f"{tag}/ Sending review at {time.time()}")
                review = await review_task
                if review:
                    await websocket.send_text(json.dumps(review))
            await websocket.send_text(json.dumps({"end_of_reviews": True}))
    except WebSocketDisconnect:
        logging.info("WebSocket disconnected")
    except Exception as e:
        logging.error(f"Error in websocket endpoint: {e}")
        logging.error(traceback.format_exc())
    finally:
        try:
            await websocket.close()
        except RuntimeError:
            logging.warning("WebSocket already closed")


# Health check endpoint
@app.get("/health")
async def health_check():
    return JSONResponse(content={"status": "healthy"})

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Grainger Recommendations API"}

@app.get("/favicon.ico")
async def favicon():
    return JSONResponse(content={"message": "No favicon available"}, status_code=204)

if __name__ == "__main__":
    import uvicorn

    port = 8000
    uvicorn.run(app, host="0.0.0.0", port=port)
