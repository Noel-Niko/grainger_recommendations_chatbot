import logging
import uuid
import io
import base64
import time
import asyncio

import httpx
import websockets
import streamlit as st
from PIL import Image
import json

tag = "StreamlitInterface"
backendUrl = "http://127.0.0.1:8000"

class StreamlitInterface:
    def __init__(self):
        self.session_id = None
        if "session_id" not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
        self.session_id = st.session_state.session_id

    def run(self):
        st.set_page_config(layout="wide")
        st.button("Clear History", on_click=self.clear_chat_history)
        st.title("Grainger Recommendations Chatbot")

        main_column, side_column = st.columns([2, 1])

        with main_column:
            self.ask_question(main_column, side_column)

    def clear_chat_history(self):
        st.session_state.chat_history = []

    def ask_question(self, center_col, col3):
        logging.info("Asking question")
        question = st.text_input("Enter your question:", value="", placeholder="", key="unique_key_for_question")
        if question:
            start_time = time.time()
            logging.info(f"Question entered: {question}")

            # Call FastAPI to process the chat question
            headers = {"session-id": self.session_id}
            payload = {"question": question, "clear_history": False}
            url = f"{backendUrl}/ask_question"

            response = self.retry_http_post(url, headers, payload, timeout=120)

            if response and response.status_code == 200:
                data = response.json()
                self.display_message(center_col, data, start_time)
                products = data['products']
                asyncio.run(self.fetch_and_display_images(col3, products))
                asyncio.run(self.websocket_reviews(center_col))
            else:
                logging.error(f"Failed to process question: {response.text if response else 'No response'}")

            total_time = time.time() - start_time
            center_col.write(f"Total time to answer question: {total_time}")

    def retry_http_post(self, url, headers, payload, timeout, retries=5, delay=5):
        """Retry HTTP POST request if it fails."""
        for attempt in range(retries):
            try:
                response = httpx.post(url, headers=headers, json=payload, timeout=timeout)
                if response.status_code == 200:
                    return response
                else:
                    logging.error(f"Attempt {attempt + 1} failed: {response.status_code} - {response.text}")
            except Exception as e:
                logging.error(f"Attempt {attempt + 1} failed: {str(e)}")
            time.sleep(delay)
        logging.error(f"All {retries} attempts failed.")
        return None

    async def fetch_and_display_images(self, col3, products):
        start_time = time.time()
        url = f"{backendUrl}/fetch_images"
        headers = {"Content-Type": "application/json", "session-id": self.session_id}
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=products, timeout=120)
            if response.status_code == 200:
                self.display_images(col3, response.json(), start_time)
            else:
                logging.error(f"Failed to fetch images: {response.text}")

    async def websocket_reviews(self, center_col):
        url = f"ws://{backendUrl}/ws/{self.session_id}"
        async with websockets.connect(url) as websocket:
            while True:
                review = await websocket.recv()
                self.display_review(center_col, json.loads(review))

    def display_message(self, center_col, data, start_time):
        center_col.subheader("Response:")
        center_col.write(data["message"])
        message_time = time.time() - start_time
        center_col.write(f"Time taken to generate message: {message_time}")
        center_col.write(f"Customer attributes identified: {data['customer_attributes_retrieved']}")
        center_col.write(f"Time taken to generate customer attributes: {data['time_to_get_attributes']}")

    def display_images(self, col3, data, start_time):
        for image_info in data:
            try:
                img = Image.open(io.BytesIO(base64.b64decode(image_info["image_data"])))
                col3.image(img, caption=f"Grainger Product Image ({image_info['code']})", use_column_width=True)
            except Exception as e:
                logging.error(f"Error displaying image: {e}")
        time_to_generate_images = time.time() - start_time
        col3.write(f"Total time taken to generate images: {time_to_generate_images}")

    def display_review(self, center_col, review):
        center_col.subheader('Extracted Reviews:')
        center_col.write(f"Product ID: {review['code']}")
        center_col.write(f"Average Star Rating: {review['average_star_rating']}")
        center_col.write(f"Average Recommendation Percent: {review['average_recommendation_percent']}")
        center_col.write("Review Texts:")
        for idx, review_text in enumerate(review['review_texts'], start=1):
            center_col.write(f"\nReview {idx}: {review_text}")

def main():
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    interface = StreamlitInterface()
    interface.run()

if __name__ == "__main__":
    main()
