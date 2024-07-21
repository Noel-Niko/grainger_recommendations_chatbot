import asyncio
import base64
import io
import logging
import os
import time
import uuid

import httpx
import streamlit as st
from PIL import Image

from ui_utils.custom_spinner import message_spinner

st.set_page_config(layout="wide")

tag = "StreamlitInterface"
backend_url = os.getenv('BACKEND_URL', 'http://127.0.0.1:8000')


class StreamlitInterface:
    def __init__(self):
        self.session_id = None
        if "session_id" not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
        self.session_id = st.session_state.session_id
        self.reviews = []
        self.polling_interval = 5
        self.polling_active = True

    def run(self):
        st.button("Clear History", on_click=self.clear_chat_history)
        st.title("Grainger Recommendations Chatbot")

        main_column, side_column = st.columns([2, 1])

        with main_column:
            self.ask_question(main_column, side_column)

        self.poll_reviews(main_column)

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
                    # Reset chat history after processing the question prn
                    if st.session_state.chat_history is True:
                        st.session_state.chat_history = False

                    response = self.retry_http_post(url, headers, payload, timeout=30, center_col=center_col)

                    if response and response.status_code == 200:
                        data = response.json()
                        self.display_message(center_col, data, start_time)
                        products = data['products']
                        st.session_state['products'] = products
                    else:
                        logging.error(f"Failed to process question: {response.text if response else 'No response'}")

                    total_time = time.time() - start_time
                    center_col.write(f"Total time to answer question: {total_time}")
                asyncio.run(self.fetch_and_display_images(col3, products))
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
                else:
                    logging.error(f"{tag} / Attempt {attempt + 1} failed: {response.status_code} - {response.text}")
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

    def poll_reviews(self, center_col):
        start_time = time.time()
        if 'products' in st.session_state:
            try:
                messages = ["Fetching reviews...", "Looking up the product codes...", "Searching on the web...",
                            "Reading reviews...", "Averaging the ratings...", "Collecting review comments..."]
                with message_spinner(messages):
                    products = st.session_state['products']
                    headers = {"Content-Type": "application/json", "session-id": self.session_id}
                    url = f"{backend_url}/fetch_reviews"
                    response = self.retry_http_post(url, headers, products, timeout=120)
                    if response and response.status_code == 200:
                        review_data = response.json()
                        new_reviews = review_data.get('reviews', [])
                        if new_reviews:
                            self.reviews.extend(new_reviews)
                            self.display_reviews(center_col, new_reviews, start_time)
                        if review_data.get('status') == 'completed':
                            self.polling_active = False
                            reviews_total_time = time.time() - start_time
                            center_col.write(f"Reviews processed in: {reviews_total_time}")
                    else:
                        logging.error(f"Failed to fetch reviews: {response.text if response else 'No response'}")

                    # Schedule the next polling
                    if self.polling_active:
                        time.sleep(self.polling_interval)
                        st.rerun()
            except Exception as e:
                logging.error(f"Error in poll_reviews: {e}")
                st.error(f"An error occurred while polling for reviews: {e}")


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

    def display_images(self, col3, data, start_time):
        try:
            with st.spinner("Displaying images..."):
                for image_info in data:
                    try:
                        img = Image.open(io.BytesIO(base64.b64decode(image_info["image_data"])))
                        col3.image(img, caption=f"Grainger Product Image ({image_info['code']})",
                                   use_column_width=True)
                    except Exception as e:
                        logging.error(f"{tag} / Error displaying image: {e}")
                time_to_generate_images = time.time() - start_time
                col3.write(f"Total time taken to generate images: {time_to_generate_images}")
        except Exception as e:
            logging.error(f"{tag} / Error displaying images: {e}")

    def display_reviews(self, center_col, reviews, start_time):
        try:
            with st.spinner("Displaying reviews..."):
                for review in reviews:
                    logging.info(f"{tag} / Displaying review: {review}")
                    if 'code' in review:
                        center_col.subheader('Extracted Review:')
                        center_col.write(f"Product ID: {review['code']}")
                        center_col.write(f"Average Star Rating: {review['average_star_rating']}")
                        center_col.write(f"Average Recommendation Percent: {review['average_recommendation_percent']}")
                        center_col.write("Review Texts:")
                        for idx, review_text in enumerate(review['review_texts'], start=1):
                            center_col.write(f"\nReview {idx}: {review_text}")
                            review_search_time = time.time() - start_time
                            center_col.write(f"\nRetrieved in: {review_search_time}")
                else:
                    logging.error(f"{tag} / Missing 'code' in review: {review}")
        except Exception as e:
            logging.error(f"{tag} / Error displaying reviews: {e}")

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
