import logging
import aiohttp
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import time
import asyncio
import httpx
import streamlit as st
import json

tag = "StreamlitInterface"

class StreamlitInterface:
    def __init__(self):
        self.session_id = None

    def initialize_session(self):
        response = httpx.get("http://localhost:8000/initialize_session")
        if response.status_code == 200:
            self.session_id = response.json().get("session_id")
            logging.info(f"{tag}/ Initialized session with ID: {self.session_id}")
        else:
            logging.error("Failed to initialize session")

    def run(self):
        st.set_page_config(layout="wide")
        st.button("Clear History", on_click=self.clear_chat_history)
        st.title("Grainger Recommendations Chatbot")

        if not self.session_id:
            self.initialize_session()

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
            url = "http://localhost:8000/ask_question"

            with st.spinner("Processing..."):
                response = asyncio.run(self.stream_events(url, headers, payload))

            for event in response:
                if event["event"] == "message":
                    self.display_message(center_col, event["data"])
                elif event["event"] == "images":
                    self.display_images(col3, event["data"])
                elif event["event"] == "reviews":
                    self.display_reviews(center_col, event["data"])

            total_time = time.time() - start_time
            center_col.write(f"Total time to answer: {total_time}")

    async def stream_events(self, url, headers, payload):
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=None)
            if response.status_code != 200:
                logging.error(f"Failed to process chat question: {response.text}")
                return []

            events = []
            event = {}
            async for line in response.aiter_lines():
                if line.strip() == "":
                    if event:
                        events.append(event)
                        event = {}
                    continue

                if line.startswith("event:"):
                    event["event"] = line[len("event:"):].strip()
                elif line.startswith("data:"):
                    data = line[len("data:"):].strip()
                    try:
                        event["data"] = json.loads(data)
                    except json.JSONDecodeError as e:
                        logging.error(f"Failed to decode JSON: {e}, line: {line}")
                else:
                    logging.warning(f"Unexpected line in SSE stream: {line}")

            return events

    def display_message(self, center_col, data):
        center_col.subheader("Response:")
        center_col.write(data["message"])
        center_col.write(f"Customer attributes identified: {data['customer_attributes_retrieved']}")
        center_col.write(f"Time taken to generate customer attributes: {data['time_to_get_attributes']}")

    def display_images(self, col3, data):
        for image_info in data:
            try:
                img = Image.open(io.BytesIO(base64.b64decode(image_info["image_data"])))
                col3.image(img, caption=f"Grainger Product Image ({image_info['code']})", use_column_width=True)
            except Exception as e:
                logging.error(f"Error displaying image: {e}")

    def display_reviews(self, center_col, data):
        center_col.subheader('Extracted Reviews:')
        for review in data:
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











# import logging
# import aiohttp
# from PIL import Image, ImageDraw, ImageFont
# import io
# import base64
# import time
# import asyncio
# import httpx
# import streamlit as st
# import json
#
# tag = "StreamlitInterface"
#
# class StreamlitInterface:
#     def __init__(self):
#         self.session_id = None
#
#     def initialize_session(self):
#         response = httpx.get("http://localhost:8000/initialize_session")
#         if response.status_code == 200:
#             self.session_id = response.json().get("session_id")
#             logging.info(f"{tag}/ Initialized session with ID: {self.session_id}")
#         else:
#             logging.error("Failed to initialize session")
#
#     def run(self):
#         st.set_page_config(layout="wide")
#         st.button("Clear History", on_click=self.clear_chat_history)
#         st.title("Grainger Recommendations Chatbot")
#
#         if not self.session_id:
#             self.initialize_session()
#
#         main_column, side_column = st.columns([2, 1])
#
#         with main_column:
#             self.ask_question(main_column, side_column)
#
#     def clear_chat_history(self):
#         st.session_state.chat_history = []
#
#     def ask_question(self, center_col, col3):
#         logging.info("Asking question")
#         question = st.text_input("Enter your question:", value="", placeholder="", key="unique_key_for_question")
#         if question:
#             start_time = time.time()
#             logging.info(f"Question entered: {question}")
#
#             # Call FastAPI to process the chat question
#             headers = {"session-id": self.session_id}
#             payload = {"question": question, "clear_history": False}
#             url = "http://localhost:8000/ask_question"
#
#             with st.spinner("Processing..."):
#                 response = asyncio.run(self.stream_events(url, headers, payload))
#
#             for event in response:
#                 if event["event"] == "message":
#                     self.display_message(center_col, event["data"])
#                 elif event["event"] == "images":
#                     self.display_images(col3, event["data"])
#                 elif event["event"] == "reviews":
#                     self.display_reviews(center_col, event["data"])
#
#             total_time = time.time() - start_time
#             center_col.write(f"Total time to answer: {total_time}")
#
#     async def stream_events(self, url, headers, payload):
#         async with httpx.AsyncClient() as client:
#             response = await client.post(url, headers=headers, json=payload, timeout=None)
#             if response.status_code != 200:
#                 logging.error(f"Failed to process chat question: {response.text}")
#                 return []
#
#             events = []
#             async for line in response.aiter_lines():
#                 if line.strip() == "":
#                     continue
#                 try:
#                     if line.startswith("data:"):
#                         event_data = line[len("data:"):].strip()
#                         event = json.loads(event_data)
#                         events.append(event)
#                     else:
#                         logging.warning(f"Unexpected line in SSE stream: {line}")
#                 except json.JSONDecodeError as e:
#                     logging.error(f"Failed to decode JSON: {e}, line: {line}")
#                     continue
#             return events
#
#     def display_message(self, center_col, data):
#         center_col.subheader("Response:")
#         center_col.write(data["message"])
#         center_col.write(f"Customer attributes identified: {data['customer_attributes_retrieved']}")
#         center_col.write(f"Time taken to generate customer attributes: {data['time_to_get_attributes']}")
#
#     def display_images(self, col3, data):
#         for image_info in data:
#             try:
#                 img = Image.open(io.BytesIO(base64.b64decode(image_info["image_data"])))
#                 col3.image(img, caption=f"Grainger Product Image ({image_info['code']})", use_column_width=True)
#             except Exception as e:
#                 logging.error(f"Error displaying image: {e}")
#
#     def display_reviews(self, center_col, data):
#         center_col.subheader('Extracted Reviews:')
#         for review in data:
#             center_col.write(f"Product ID: {review['code']}")
#             center_col.write(f"Average Star Rating: {review['average_star_rating']}")
#             center_col.write(f"Average Recommendation Percent: {review['average_recommendation_percent']}")
#             center_col.write("Review Texts:")
#             for idx, review_text in enumerate(review['review_texts'], start=1):
#                 center_col.write(f"\nReview {idx}: {review_text}")
#
# def main():
#     if 'chat_history' not in st.session_state:
#         st.session_state.chat_history = []
#
#     interface = StreamlitInterface()
#     interface.run()
#
# if __name__ == "__main__":
#     main()
#
#
#
#
