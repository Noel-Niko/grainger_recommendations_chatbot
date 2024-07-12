from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import io

from image_utils.grainger_image_util import get_images
from vector_index.chat_processor import process_chat_question_with_customer_attribute_identifier
from vector_index.document import initialize_embeddings_and_faiss, parallel_search
from web_extraction_tools.product_reviews.call_selenium_for_review_async import async_navigate_to_reviews_selenium

app = FastAPI()


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


# Initialize the state and dependencies
@app.on_event("startup")
async def startup_event():
    global vectorstore_faiss_doc, bedrock_embeddings, df, llm, driver
    bedrock_embeddings, vectorstore_faiss_doc, df, llm = initialize_embeddings_and_faiss()
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)


@app.on_event("shutdown")
async def shutdown_event():
    driver.quit()


@app.post("/ask_question", response_model=ChatResponse)
async def ask_question(chat_request: ChatRequest):
    try:
        start_time = time.time()
        message, response_json, customer_attributes_retrieved, time_to_get_attributes = await process_chat_question(
            chat_request.question, chat_request.clear_history)

        time_taken = time.time() - start_time
        return ChatResponse(
            message=message,
            response_json=response_json,
            time_taken=time_taken,
            customer_attributes_retrieved=customer_attributes_retrieved,
            time_to_get_attributes=time_to_get_attributes
        )
    except Exception as e:
        logging.error(f"Error in chat processing: {e}")
        raise HTTPException(status_code=500, detail="Error processing chat question")


async def process_chat_question(question, clear_history):
    try:
        if clear_history:
            logging.info("Clearing chat history")
            if 'chat_history' in st.session_state:
                st.session_state.chat_history.clear()
            else:
                st.session_state.chat_history = []

        message, response_json, customer_attributes_retrieved, time_to_get_attributes = process_chat_question_with_customer_attribute_identifier(
            question,
            vectorstore_faiss_doc,
            llm,
            st.session_state.chat_history if 'chat_history' in st.session_state else []
        )

        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        st.session_state.chat_history.append(
            [f"QUESTION: {question}. MESSAGE: {message}. CUSTOMER ATTRIBUTES: {customer_attributes_retrieved}"])

        return message, response_json, customer_attributes_retrieved, time_to_get_attributes
    except Exception as e:
        logging.error(f"Error in chat processing: {e}")
        raise e


@app.post("/fetch_images", response_model=list[ImageResponse])
async def fetch_images(products: list[dict]):
    try:
        recommendations_list = [f"{product['product']}, {product['code']}" for product in products]
        image_data, total_image_time = await get_images(recommendations_list, df)

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
        raise HTTPException(status_code=500, detail="Error fetching images")


@app.post("/fetch_reviews")
async def fetch_reviews(products: list[dict]):
    try:
        reviews = []
        for product in products:
            product_info = f"{product['product']}, {product['code']}"
            reviews_data = await async_navigate_to_reviews_selenium(product_info, driver)
            if reviews_data:
                reviews.append({
                    "code": product['code'],
                    "average_star_rating": reviews_data['Average Star Rating'],
                    "average_recommendation_percent": reviews_data['Average Recommendation Percent'],
                    "review_texts": reviews_data['Review Texts']
                })
        return reviews
    except Exception as e:
        logging.error(f"Error fetching reviews: {e}")
        raise HTTPException(status_code=500, detail="Error fetching reviews")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
