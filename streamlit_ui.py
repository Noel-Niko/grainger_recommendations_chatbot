import os
import streamlit as st
import logging
import uuid
import io
import base64
import time
import asyncio
import httpx
from PIL import Image
import json
from modules.vector_index.utils.custom_spinner import message_spinner

st.set_page_config(layout="wide")

tag = "StreamlitInterface"
backend_url = os.getenv('BACKEND_URL', 'http://127.0.0.1:8000')

class StreamlitInterface:
    def __init__(self):
        self.session_id = None
        if "session_id" not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
        self.session_id = st.session_state.session_id

    def run(self):
        st.button("Clear History", on_click=self.clear_chat_history)
        st.title("Grainger Recommendations Chatbot")

        main_column, side_column = st.columns([2, 1])

        with main_column:
            self.ask_question(main_column, side_column)

    def clear_chat_history(self):
        st.session_state.chat_history = True

    def ask_question(self, center_col, col3):
        logging.info("Asking question")
        question = st.text_input("Enter your question:", value="", placeholder="", key="unique_key_for_question")
        if question:
            try:
                messages = ["Processing...", "Loading data...", "Running analysis...",
                            "Comparing results to your question...", "Almost there..."]
                with message_spinner(messages):
                    start_time = time.time()
                    logging.info(f"Question entered: {question}")

                    # Call FastAPI to process the chat question
                    headers = {"session-id": self.session_id}
                    payload = {"session_id": self.session_id, "question": question,
                               "clear_history": st.session_state.chat_history}
                    url = f"{backend_url}/ask_question"
                    # Reset chat history after processing the question
                    if st.session_state.chat_history is True:
                        st.session_state.chat_history = False

                    response = self.retry_http_post(url, headers, payload, timeout=20, center_col=center_col)

                    if response and response.status_code == 200:
                        data = response.json()
                        self.display_message(center_col, data, start_time)
                        products = data['products']
                    else:
                        logging.error(f"Failed to process question: {response.text if response else 'No response'}")

                    total_time = time.time() - start_time
                    center_col.write(f"Total time to answer question: {total_time}")
                asyncio.run(self.fetch_and_display_images(col3, products))
                asyncio.run(self.fetch_reviews(center_col, products))
            except Exception as e:
                logging.error(f"Error in ask_question: {e}")
                st.error(f"An error occurred while processing the question: {e}")

    def retry_http_post(self, url, headers, payload, timeout, retries=5, delay=1, center_col=None):
        """Retry HTTP POST request if it fails."""
        for attempt in range(retries):
            try:
                response = httpx.post(url, headers=headers, json=payload, timeout=timeout)
                if response.status_code == 200:
                    logging.info(f"{tag} / Attempt {attempt + 1} successful returning response")
                    return response
                # else:
                #     logging.error(f"{tag} / Attempt {attempt + 1} failed: {response.status_code} - {response.text}")
            except Exception as e:
                logging.error(f"{tag} / Attempt {attempt + 1} failed: {str(e)}")
            time.sleep(delay)
        logging.error(f"{tag} / All {retries} attempts failed.")
        center_col.write("Sorry unable to process your request. Please try again.")
        return None

    async def fetch_and_display_images(self, col3, products):
        try:
            with st.spinner("Fetching images..."):
                start_time = time.time()
                url = f"{backend_url}/fetch_images"
                headers = {"Content-Type": "application/json", "session-id": self.session_id}
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, headers=headers, json=products, timeout=120)
                    if response.status_code == 200:
                        self.display_images(col3, response.json(), start_time)
                    else:
                        logging.error(f"Failed to fetch images: {response.text}")
        except Exception as e:
            logging.error(f"Error fetching images: {e}")
            st.error(f"An error occurred while fetching images: {e}")

    async def fetch_reviews(self, center_col, products):
        try:
            messages = ["Fetching reviews...", "Looking up the product codes...", "Searching on the web...",
                        "Reading reviews...", "Averaging the ratings...", "Collecting review comments..."]
            with message_spinner(messages):
                semaphore = asyncio.Semaphore(10)
                async with httpx.AsyncClient() as client:
                    tasks = [self.fetch_review_for_product(product, client, semaphore) for product in products]
                    reviews = await asyncio.gather(*tasks)
                    for review in reviews:
                        if review:
                            self.display_review(center_col, review)
        except Exception as e:
            logging.error(f"{tag} / Error in fetch_reviews: {e}")
            st.error(f"{tag} / An error occurred while fetching reviews: {e}")

    async def fetch_review_for_product(self, product, client, semaphore):
        async with semaphore:
            product_info = f"{product['product']}, {product['code']}"
            logging.info(f"{tag}/ Fetching reviews for product: {product_info}")

            try:
                url = f"{backend_url}/fetch_review"
                payload = {"product_info": product_info}
                headers = {"Content-Type": "application/json", "session-id": self.session_id}
                response = await client.post(url, headers=headers, json=payload, timeout=60)
                if response.status_code == 200:
                    reviews_data = response.json()
                    review = {
                        "code": product['code'],
                        "average_star_rating": reviews_data['Average Star Rating'],
                        "average_recommendation_percent": reviews_data['Average Recommendation Percent'],
                        "review_texts": reviews_data['Review Texts']
                    }
                    logging.info(f"{tag}/ Reviews for product {product['code']}: {reviews_data}")
                    return review
                else:
                    logging.error(f"{tag}/ Failed to fetch reviews for product {product['code']}: {response.text}")
                    return None
            except Exception as e:
                logging.error(f"{tag}/ Error fetching reviews for product {product['code']}: {str(e)}")
                return None

    def display_message(self, center_col, data, start_time):
        try:
            with st.spinner("Displaying message..."):
                center_col.subheader("Response:")
                center_col.write(data["message"])
                message_time = time.time() - start_time
                center_col.write(f"Time taken to generate message: {message_time}")
                center_col.write(f"Customer attributes identified: {data['customer_attributes_retrieved']}")
                center_col.write(f"Time taken to generate customer attributes: {data['time_to_get_attributes']}")
        except Exception as e:
            logging.error(f"{tag} / Error displaying message: {e}")
            st.error(f"{tag} / An error occurred while displaying message: {e}")

    def display_images(self, col3, data, start_time):
        try:
            with st.spinner("Displaying images..."):
                for image_info in data:
                    try:
                        img = Image.open(io.BytesIO(base64.b64decode(image_info["image_data"])))
                        col3.image(img, caption=f"{tag} / Grainger Product Image ({image_info['code']})",
                                   use_column_width=True)
                    except Exception as e:
                        logging.error(f"{tag} / Error displaying image: {e}")
                time_to_generate_images = time.time() - start_time
                col3.write(f"Total time taken to generate images: {time_to_generate_images}")
        except Exception as e:
            logging.error(f"{tag} / Error displaying images: {e}")
            st.error(f"{tag} / An error occurred while displaying images: {e}")

    def display_review(self, center_col, review):
        try:
            with st.spinner("Displaying review..."):
                logging.info(f"{tag} / Displaying review: {review}")
                if 'code' in review:
                    center_col.subheader('Extracted Review:')
                    center_col.write(f"Product ID: {review['code']}")
                    center_col.write(f"Average Star Rating: {review['average_star_rating']}")
                    center_col.write(f"Average Recommendation Percent: {review['average_recommendation_percent']}")
                    center_col.write("Review Texts:")
                    for idx, review_text in enumerate(review['review_texts'], start=1):
                        center_col.write(f"\nReview {idx}: {review_text}")
                else:
                    logging.error(f"{tag} / Missing 'code' in review: {review}")
        except Exception as e:
            logging.error(f"{tag} / Error displaying review: {e}")
            st.error(f"{tag} / An error occurred while displaying review: {e}")

    # Health check endpoint
    if st.query_params.get("health"):
        st.write("ok")


def main():
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = False

    interface = StreamlitInterface()
    interface.run()


if __name__ == "__main__":
    main()
