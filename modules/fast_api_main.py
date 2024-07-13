import json
import logging
import sys
import uuid
import time
import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import io
import traceback

from modules.image_utils.grainger_image_util import get_images
from modules.vector_index.chat_processor import process_chat_question_with_customer_attribute_identifier
from modules.vector_index.document import initialize_embeddings_and_faiss, parallel_search
from modules.web_extraction_tools.product_reviews.call_selenium_for_review_async import \
    async_navigate_to_reviews_selenium
from fastapi.middleware.cors import CORSMiddleware

tag = "fast_api_main"
app = FastAPI()

session_store = {}

logging.basicConfig(level=logging.INFO)


class ChatRequest(BaseModel):
    question: str
    clear_history: bool = False


class ChatResponse(BaseModel):
    message: str
    response_json: dict
    time_taken: float
    customer_attributes_retrieved: dict
    time_to_get_attributes: float


class ImageResponse(BaseModel):
    code: str
    image_data: bytes


@app.on_event("startup")
async def startup_event():
    global vectorstore_faiss_doc, bedrock_embeddings, df, llm, driver
    try:
        bedrock_embeddings, vectorstore_faiss_doc, df, llm = initialize_embeddings_and_faiss()
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        logging.info("Startup complete.")
    except Exception as e:
        logging.error(f"Error during startup: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    try:
        driver.quit()
        logging.info("Shutdown complete.")
    except Exception as e:
        logging.error(f"Error during shutdown: {str(e)}")


@app.get("/initialize_session")
async def initialize_session():
    session_id = str(uuid.uuid4())
    session_store[session_id] = []  # Initialize an empty chat history for this session
    logging.info(f"{tag}/ Session initialized with ID: {session_id}")
    return {"session_id": session_id}


@app.post("/ask_question", response_model=ChatResponse)
async def ask_question(chat_request: ChatRequest, request: Request):
    try:
        session_id = request.headers.get("session-id")
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID is required")

        if session_id not in session_store:
            logging.error(f"Session ID {session_id} not found in session_store")
            raise HTTPException(status_code=400, detail="Invalid Session ID")

        start_time = time.time()
        logging.info(f"{tag}/ Received question: {chat_request.question} with session_id: {session_id}")
        message, response_json, customer_attributes_retrieved, time_to_get_attributes = await process_chat_question(
            chat_request.question, chat_request.clear_history, session_id)

        if response_json is None:
            logging.error(f"{tag}/ Response json is None")
            raise HTTPException(status_code=500, detail="Error processing chat question, response is None")

        products = response_json.get('products', [])
        logging.info(f"{tag}/ Products retrieved: {products}")

        # Use asyncio.gather to await multiple async functions concurrently
        image_data, reviews_data = await asyncio.gather(
            fetch_images(products),
            fetch_reviews(products)
        )

        time_taken = time.time() - start_time
        logging.info(f"{tag}/ Total time taken for ask_question: {time_taken} seconds")
        # Ensure response_json is not None
        if response_json is None:
            logging.error(f"{tag}/ Response json is None")
            raise HTTPException(status_code=500, detail="Error processing chat question, response is None")

        chat_response = ChatResponse(
            message=message,
            response_json=response_json,
            time_taken=time_taken,
            customer_attributes_retrieved=json.loads(customer_attributes_retrieved) if isinstance(
                customer_attributes_retrieved, str) else customer_attributes_retrieved,
            time_to_get_attributes=time_to_get_attributes
        )

        logging.info(f"{tag}/ Returning ChatResponse: {chat_response.json()}")
        return chat_response
    except Exception as e:
        logging.error(f"Error in {tag}/ask_question: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def process_chat_question(question, clear_history, session_id):
    try:
        if clear_history:
            logging.info(f"{tag}/ Clearing chat history for session_id: {session_id}")
            session_store[session_id] = []

        chat_history = session_store.get(session_id, [])
        logging.info(f"{tag}/ Current chat history for session_id {session_id}: {chat_history}")

        logging.info(f"{tag}/ Processing question: {question}")
        message, response_json, customer_attributes_retrieved, time_to_get_attributes = process_chat_question_with_customer_attribute_identifier(
            question,
            vectorstore_faiss_doc,
            llm,
            chat_history
        )
        logging.info(f"{tag}/ Message: {message}")
        logging.info(f"{tag}/ Response json: {response_json}")
        logging.info(f"{tag}/ Customer attributes retrieved: {customer_attributes_retrieved}")
        logging.info(f"{tag}/ Time to get attributes: {time_to_get_attributes}")
        session_store[session_id].append(
            [f"QUESTION: {question}. MESSAGE: {message}. CUSTOMER ATTRIBUTES: {customer_attributes_retrieved}"])
        logging.info(f"{tag}/ Updated chat history for session_id {session_id}: {session_store[session_id]}")
        logging.info(f"{tag}/ Processed question: {question} with message: {message}")

        return message, response_json, customer_attributes_retrieved, time_to_get_attributes
    except Exception as e:
        logging.error(f"{tag}/ Error processing chat question: {str(e)}")
        logging.error(traceback.format_exc())
        raise


async def fetch_images(products):
    try:
        recommendations_list = [f"{product['product']}, {product['code']}" for product in products]
        logging.info(f"{tag}/ Fetching images for products: {recommendations_list}")
        image_data, total_image_time = await get_images(recommendations_list, df)
        logging.info(f"{tag}/ Total time to fetch images: {total_image_time} seconds")

        image_responses = []
        for image_info in image_data:
            try:
                img = Image.open(io.BytesIO(image_info["Image Data"]))
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                image_responses.append(ImageResponse(code=image_info["Code"], image_data=img_byte_arr))
            except Exception as e:
                logging.error(f"Error displaying image: {e}")
        return image_responses
    except Exception as e:
        logging.error(f"Error fetching images: {e}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error fetching images")


async def fetch_reviews(products):
    try:
        reviews = []
        for product in products:
            product_info = f"{product['product']}, {product['code']}"
            logging.info(f"{tag}/ Fetching reviews for product: {product_info}")
            reviews_data = await async_navigate_to_reviews_selenium(product_info, driver)
            if reviews_data:
                reviews.append({
                    "code": product['code'],
                    "average_star_rating": reviews_data['Average Star Rating'],
                    "average_recommendation_percent": reviews_data['Average Recommendation Percent'],
                    "review_texts": reviews_data['Review Texts']
                })
                logging.info(f"{tag}/ Reviews for product {product['code']}: {reviews_data}")
            else:
                logging.info(f"{tag}/ No reviews found for product {product['code']}")
        return reviews
    except Exception as e:
        logging.error(f"Error fetching reviews: {e}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error fetching reviews")


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

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    uvicorn.run(app, host="0.0.0.0", port=port)

# import json
# import logging
# import sys
# import uuid
# import time
# import asyncio
# from fastapi import FastAPI, HTTPException, Request
# from fastapi.responses import JSONResponse
# from pydantic import BaseModel
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from PIL import Image
# import io
# import traceback
#
# from modules.image_utils.grainger_image_util import get_images
# from modules.vector_index.chat_processor import process_chat_question_with_customer_attribute_identifier
# from modules.vector_index.document import initialize_embeddings_and_faiss, parallel_search
# from modules.web_extraction_tools.product_reviews.call_selenium_for_review_async import \
#     async_navigate_to_reviews_selenium
# from fastapi.middleware.cors import CORSMiddleware
#
# tag = "fast_api_main"
# app = FastAPI()
#
# # app.add_middleware(
# #     CORSMiddleware,
# #     allow_origins=["*"],  # Change this to frontend URL in production
# #     allow_credentials=True,
# #     allow_methods=["*"],
# #     allow_headers=["*"],
# # )
#
# session_store = {}
#
# logging.basicConfig(level=logging.INFO)
#
#
# class ChatRequest(BaseModel):
#     question: str
#     clear_history: bool = False
#
#
# class ChatResponse(BaseModel):
#     message: str
#     response_json: dict
#     time_taken: float
#     customer_attributes_retrieved: dict
#     time_to_get_attributes: float
#
#
# class ImageResponse(BaseModel):
#     code: str
#     image_data: bytes
#
#
# @app.on_event("startup")
# async def startup_event():
#     global vectorstore_faiss_doc, bedrock_embeddings, df, llm, driver
#     try:
#         bedrock_embeddings, vectorstore_faiss_doc, df, llm = initialize_embeddings_and_faiss()
#         options = Options()
#         options.add_argument("--headless")
#         options.add_argument("--disable-gpu")
#         service = Service(ChromeDriverManager().install())
#         driver = webdriver.Chrome(service=service, options=options)
#         logging.info("Startup complete.")
#     except Exception as e:
#         logging.error(f"Error during startup: {str(e)}")
#
#
# @app.on_event("shutdown")
# async def shutdown_event():
#     try:
#         driver.quit()
#         logging.info("Shutdown complete.")
#     except Exception as e:
#         logging.error(f"Error during shutdown: {str(e)}")
#
#
# @app.get("/initialize_session")
# async def initialize_session():
#     session_id = str(uuid.uuid4())
#     session_store[session_id] = []  # Initialize an empty chat history for this session
#     logging.info(f"{tag}/ Session initialized with ID: {session_id}")
#     return {"session_id": session_id}
#
#
# @app.post("/ask_question", response_model=ChatResponse)
# async def ask_question(chat_request: ChatRequest, request: Request):
#     try:
#         session_id = request.headers.get("session-id")
#         if not session_id:
#             raise HTTPException(status_code=400, detail="Session ID is required")
#
#         if session_id not in session_store:
#             logging.error(f"Session ID {session_id} not found in session_store")
#             raise HTTPException(status_code=400, detail="Invalid Session ID")
#
#         start_time = time.time()
#         logging.info(f"{tag}/ Received question: {chat_request.question} with session_id: {session_id}")
#         message, response_json, customer_attributes_retrieved, time_to_get_attributes = await process_chat_question(
#             chat_request.question, chat_request.clear_history, session_id)
#
#         products = response_json.get('products', [])
#         logging.info(f"{tag}/ Products retrieved: {products}")
#
#         # Use asyncio.gather to await multiple async functions concurrently
#         image_data, reviews_data = await asyncio.gather(
#             fetch_images(products),
#             fetch_reviews(products)
#         )
#
#         time_taken = time.time() - start_time
#         logging.info(f"{tag}/ Total time taken for ask_question: {time_taken} seconds")
#
#         return ChatResponse(
#             message=message,
#             response_json=response_json,
#             time_taken=time_taken,
#             customer_attributes_retrieved=json.loads(customer_attributes_retrieved) if isinstance(
#                 customer_attributes_retrieved, str) else customer_attributes_retrieved,
#             time_to_get_attributes=time_to_get_attributes
#         )
#     except Exception as e:
#         logging.error(f"Error in /ask_question: {str(e)}")
#         logging.error(traceback.format_exc())
#         raise HTTPException(status_code=500, detail="Internal Server Error")
#
#
# async def process_chat_question(question, clear_history, session_id):
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
#             vectorstore_faiss_doc,
#             llm,
#             chat_history
#         )
#         logging.info(f"{tag}/ Message: {message}")
#         logging.info(f"{tag}/ Response json: {response_json}")
#         logging.info(f"{tag}/ Customer attributes retrieved: {customer_attributes_retrieved}")
#         logging.info(f"{tag}/ Time to get attributes: {time_to_get_attributes}")
#         session_store[session_id].append(
#             [f"QUESTION: {question}. MESSAGE: {message}. CUSTOMER ATTRIBUTES: {customer_attributes_retrieved}"])
#         logging.info(f"{tag}/ Updated chat history for session_id {session_id}: {session_store[session_id]}")
#         logging.info(f"{tag}/ Processed question: {question} with message: {message}")
#
#         return message, response_json, customer_attributes_retrieved, time_to_get_attributes
#     except Exception as e:
#         logging.error(f"Error processing chat question: {str(e)}")
#         logging.error(traceback.format_exc())
#         raise
#
#
# async def fetch_images(products):
#     try:
#         recommendations_list = [f"{product['product']}, {product['code']}" for product in products]
#         logging.info(f"{tag}/ Fetching images for products: {recommendations_list}")
#         image_data, total_image_time = await get_images(recommendations_list, df)
#         logging.info(f"{tag}/ Total time to fetch images: {total_image_time} seconds")
#
#         image_responses = []
#         for image_info in image_data:
#             try:
#                 img = Image.open(io.BytesIO(image_info["Image Data"]))
#                 img_byte_arr = io.BytesIO()
#                 img.save(img_byte_arr, format='PNG')
#                 img_byte_arr = img_byte_arr.getvalue()
#                 image_responses.append(ImageResponse(code=image_info["Code"], image_data=img_byte_arr))
#             except Exception as e:
#                 logging.error(f"Error displaying image: {e}")
#         return image_responses
#     except Exception as e:
#         logging.error(f"Error fetching images: {e}")
#         logging.error(traceback.format_exc())
#         raise HTTPException(status_code=500, detail="Error fetching images")
#
#
# async def fetch_reviews(products):
#     try:
#         reviews = []
#         for product in products:
#             product_info = f"{product['product']}, {product['code']}"
#             logging.info(f"{tag}/ Fetching reviews for product: {product_info}")
#             reviews_data = await async_navigate_to_reviews_selenium(product_info, driver)
#             if reviews_data:
#                 reviews.append({
#                     "code": product['code'],
#                     "average_star_rating": reviews_data['Average Star Rating'],
#                     "average_recommendation_percent": reviews_data['Average Recommendation Percent'],
#                     "review_texts": reviews_data['Review Texts']
#                 })
#                 logging.info(f"{tag}/ Reviews for product {product['code']}: {reviews_data}")
#             else:
#                 logging.info(f"{tag}/ No reviews found for product {product['code']}")
#         return reviews
#     except Exception as e:
#         logging.error(f"Error fetching reviews: {e}")
#         logging.error(traceback.format_exc())
#         raise HTTPException(status_code=500, detail="Error fetching reviews")
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
#     port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
#     uvicorn.run(app, host="0.0.0.0", port=port)
#
# # import logging
# # import sys
# # import uuid
# # import time
# # import asyncio
# # from fastapi import FastAPI, HTTPException, Request
# # from fastapi.responses import JSONResponse
# # from pydantic import BaseModel
# # from selenium import webdriver
# # from selenium.webdriver.chrome.options import Options
# # from selenium.webdriver.chrome.service import Service
# # from webdriver_manager.chrome import ChromeDriverManager
# # from PIL import Image
# # import io
# # import traceback
# #
# # from modules.image_utils.grainger_image_util import get_images
# # from modules.vector_index.chat_processor import process_chat_question_with_customer_attribute_identifier
# # from modules.vector_index.document import initialize_embeddings_and_faiss, parallel_search
# # from modules.web_extraction_tools.product_reviews.call_selenium_for_review_async import async_navigate_to_reviews_selenium
# # from fastapi.middleware.cors import CORSMiddleware
# #
# # app = FastAPI()
# #
# # app.add_middleware(
# #     CORSMiddleware,
# #     allow_origins=["*"],  # Change this to frontend URL in production
# #     allow_credentials=True,
# #     allow_methods=["*"],
# #     allow_headers=["*"],
# # )
# #
# # session_store = {}
# #
# # logging.basicConfig(level=logging.INFO)
# #
# # class ChatRequest(BaseModel):
# #     question: str
# #     clear_history: bool = False
# #
# # class ChatResponse(BaseModel):
# #     message: str
# #     response_json: dict
# #     time_taken: float
# #     customer_attributes_retrieved: dict
# #     time_to_get_attributes: float
# #
# # class ImageResponse(BaseModel):
# #     code: str
# #     image_data: bytes
# #
# # @app.on_event("startup")
# # async def startup_event():
# #     global vectorstore_faiss_doc, bedrock_embeddings, df, llm, driver
# #     try:
# #         bedrock_embeddings, vectorstore_faiss_doc, df, llm = initialize_embeddings_and_faiss()
# #         options = Options()
# #         options.add_argument("--headless")
# #         options.add_argument("--disable-gpu")
# #         service = Service(ChromeDriverManager().install())
# #         driver = webdriver.Chrome(service=service, options=options)
# #         logging.info("Startup complete.")
# #     except Exception as e:
# #         logging.error(f"Error during startup: {str(e)}")
# #
# # @app.on_event("shutdown")
# # async def shutdown_event():
# #     try:
# #         driver.quit()
# #         logging.info("Shutdown complete.")
# #     except Exception as e:
# #         logging.error(f"Error during shutdown: {str(e)}")
# #
# # @app.get("/initialize_session")
# # async def initialize_session():
# #     session_id = str(uuid.uuid4())
# #     session_store[session_id] = []  # Initialize an empty chat history for this session
# #     return {"session_id": session_id}
# #
# # @app.post("/ask_question", response_model=ChatResponse)
# # async def ask_question(chat_request: ChatRequest, request: Request):
# #     try:
# #         session_id = request.headers.get("session-id")
# #         if not session_id:
# #             raise HTTPException(status_code=400, detail="Session ID is required")
# #
# #         start_time = time.time()
# #         logging.info(f"{tag}/ Received question: {chat_request.question} with session_id: {session_id}")
# #         message, response_json, customer_attributes_retrieved, time_to_get_attributes = await process_chat_question(
# #             chat_request.question, chat_request.clear_history, session_id)
# #
# #         products = response_json.get('products', [])
# #         logging.info(f"{tag}/ Products retrieved: {products}")
# #
# #         # Use asyncio.gather to await multiple async functions concurrently
# #         image_data, reviews_data = await asyncio.gather(
# #             fetch_images(products),
# #             fetch_reviews(products)
# #         )
# #
# #         time_taken = time.time() - start_time
# #         logging.info(f"{tag}/ Total time taken for ask_question: {time_taken} seconds")
# #
# #         return ChatResponse(
# #             message=message,
# #             response_json=response_json,
# #             time_taken=time_taken,
# #             customer_attributes_retrieved=customer_attributes_retrieved,
# #             time_to_get_attributes=time_to_get_attributes
# #         )
# #     except Exception as e:
# #         logging.error(f"Error in /ask_question: {str(e)}")
# #         logging.error(traceback.format_exc())
# #         raise HTTPException(status_code=500, detail="Internal Server Error")
# #
# # async def process_chat_question(question, clear_history, session_id):
# #     try:
# #         if clear_history:
# #             logging.info("Clearing chat history for session_id: {session_id}")
# #             session_store[session_id] = []
# #
# #         chat_history = session_store.get(session_id, [])
# #         logging.info(f"{tag}/ Current chat history for session_id {session_id}: {chat_history}")
# #
# #         logging.info(f"{tag}/ Processing question: {question}")
# #         message, response_json, customer_attributes_retrieved, time_to_get_attributes = process_chat_question_with_customer_attribute_identifier(
# #             question,
# #             vectorstore_faiss_doc,
# #             llm,
# #             chat_history
# #         )
# #         logging.info(f"{tag}/ Message: {message}")
# #         logging.info(f"{tag}/ Response json: {response_json}")
# #         logging.info(f"{tag}/ Customer attributes retrieved: {customer_attributes_retrieved}")
# #         logging.info(f"{tag}/ Time to get attributes: {time_to_get_attributes}")
# #         session_store[session_id].append(
# #             [f"QUESTION: {question}. MESSAGE: {message}. CUSTOMER ATTRIBUTES: {customer_attributes_retrieved}"])
# #         logging.info(f"{tag}/ Updated chat history for session_id {session_id}: {session_store[session_id]}")
# #         logging.info(f"{tag}/ Processed question: {question} with message: {message}")
# #
# #         return message, response_json, customer_attributes_retrieved, time_to_get_attributes
# #     except Exception as e:
# #         logging.error(f"Error processing chat question: {str(e)}")
# #         logging.error(traceback.format_exc())
# #         raise
# #
# # async def fetch_images(products):
# #     try:
# #         recommendations_list = [f"{product['product']}, {product['code']}" for product in products]
# #         logging.info(f"{tag}/ Fetching images for products: {recommendations_list}")
# #         image_data, total_image_time = await get_images(recommendations_list, df)
# #         logging.info(f"{tag}/ Total time to fetch images: {total_image_time} seconds")
# #
# #         image_responses = []
# #         for image_info in image_data:
# #             try:
# #                 img = Image.open(io.BytesIO(image_info["Image Data"]))
# #                 img_byte_arr = io.BytesIO()
# #                 img.save(img_byte_arr, format='PNG')
# #                 img_byte_arr = img_byte_arr.getvalue()
# #                 image_responses.append(ImageResponse(code=image_info["Code"], image_data=img_byte_arr))
# #             except Exception as e:
# #                 logging.error(f"Error displaying image: {e}")
# #         return image_responses
# #     except Exception as e:
# #         logging.error(f"Error fetching images: {e}")
# #         logging.error(traceback.format_exc())
# #         raise HTTPException(status_code=500, detail="Error fetching images")
# #
# # async def fetch_reviews(products):
# #     try:
# #         reviews = []
# #         for product in products:
# #             product_info = f"{product['product']}, {product['code']}"
# #             logging.info(f"{tag}/ Fetching reviews for product: {product_info}")
# #             reviews_data = await async_navigate_to_reviews_selenium(product_info, driver)
# #             if reviews_data:
# #                 reviews.append({
# #                     "code": product['code'],
# #                     "average_star_rating": reviews_data['Average Star Rating'],
# #                     "average_recommendation_percent": reviews_data['Average Recommendation Percent'],
# #                     "review_texts": reviews_data['Review Texts']
# #                 })
# #                 logging.info(f"{tag}/ Reviews for product {product['code']}: {reviews_data}")
# #             else:
# #                 logging.info(f"{tag}/ No reviews found for product {product['code']}")
# #         return reviews
# #     except Exception as e:
# #         logging.error(f"Error fetching reviews: {e}")
# #         logging.error(traceback.format_exc())
# #         raise HTTPException(status_code=500, detail="Error fetching reviews")
# #
# # # Health check endpoint
# # @app.get("/health")
# # async def health_check():
# #     return JSONResponse(content={"status": "healthy"})
# #
# # @app.get("/")
# # async def read_root():
# #     return {"message": "Welcome to the Grainger Recommendations API"}
# #
# # @app.get("/favicon.ico")
# # async def favicon():
# #     return JSONResponse(content={"message": "No favicon available"}, status_code=204)
# #
# # if __name__ == "__main__":
# #     import uvicorn
# #     port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
# #     uvicorn.run(app, host="0.0.0.0", port=port)
# #
# #
# #
