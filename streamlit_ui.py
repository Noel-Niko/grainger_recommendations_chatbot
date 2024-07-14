import logging
from PIL import Image
import io
import base64
import time
import asyncio
import httpx
import streamlit as st
import json

tag = "StreamlitInterface"
backendUrl = "http://127.0.0.1:8000"

class StreamlitInterface:
    def __init__(self):
        self.session_id = None

    def initialize_session(self):
        response = httpx.get(f"{backendUrl}/initialize_session")
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
            url = f"{backendUrl}/ask_question"

            with st.spinner("Processing..."):
                response = httpx.post(url, headers=headers, json=payload, timeout=120)

            if response.status_code == 200:
                data = response.json()
                self.display_message(center_col, data)
                products = data['products']
                asyncio.run(self.fetch_and_display_images(col3, products))
                asyncio.run(self.fetch_and_display_reviews(center_col, products))
            else:
                logging.error(f"Failed to process question: {response.text}")

            total_time = time.time() - start_time
            center_col.write(f"Total time to answer: {total_time}")

    async def fetch_and_display_images(self, col3, products):
        url = f"{backendUrl}/fetch_images"
        headers = {"Content-Type": "application/json"}
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=products, timeout=120)
            if response.status_code == 200:
                self.display_images(col3, response.json())
            else:
                logging.error(f"Failed to fetch images: {response.text}")

    async def fetch_and_display_reviews(self, center_col, products):
        url = f"{backendUrl}/fetch_reviews"
        headers = {"Content-Type": "application/json"}
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=products, timeout=120)
            if response.status_code == 200:
                self.display_reviews(center_col, response.json())
            else:
                logging.error(f"Failed to fetch reviews: {response.text}")

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
# from PIL import Image
# import io
# import base64
# import time
# import asyncio
# import httpx
# import streamlit as st
# import json
#
# tag = "StreamlitInterface"
# backendUrl = "http://127.0.0.1:8000"
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
#             url = f"{backendUrl}/ask_question"
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
#                 return
#
#             async for line in response.aiter_lines():
#                 if line.strip() == "":
#                     continue
#
#                 if line.startswith("event:"):
#                     event_type = line[len("event:"):].strip()
#                 elif line.startswith("data:"):
#                     data = line[len("data:"):].strip()
#                     try:
#                         data_dict = json.loads(data)
#                         if event_type == "message":
#                             self.display_message(None,
#                                                  data_dict)  # Assuming display_message can handle no column parameter
#                         elif event_type == "images":
#                             self.display_images(None, data_dict)  # Adjust according to your display methods
#                         elif event_type == "reviews":
#                             self.display_reviews(None, data_dict)  # Adjust according to your display methods
#                     except json.JSONDecodeError as e:
#                         logging.error(f"Failed to decode JSON: {e}, line: {line}")
#
#     def display_message(self, center_col, data):
#         if isinstance(data, str):
#             data = json.loads(data)
#         center_col.subheader("Response:")
#         center_col.write(data["message"])
#         center_col.write(f"Customer attributes identified: {data['customer_attributes_retrieved']}")
#         center_col.write(f"Time taken to generate customer attributes: {data['time_to_get_attributes']}")
#
#     def display_images(self, col3, data):
#         if isinstance(data, str):
#             data = json.loads(data)
#         for image_info in data:
#             try:
#                 img = Image.open(io.BytesIO(base64.b64decode(image_info["image_data"])))
#                 col3.image(img, caption=f"Grainger Product Image ({image_info['code']})", use_column_width=True)
#             except Exception as e:
#                 logging.error(f"Error displaying image: {e}")
#
#     def display_reviews(self, center_col, data):
#         if isinstance(data, str):
#             data = json.loads(data)
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
#             event = {}
#             async for line in response.aiter_lines():
#                 if line.strip() == "":
#                     if event:
#                         events.append(event)
#                         event = {}
#                     continue
#
#                 if line.startswith("event:"):
#                     event["event"] = line[len("event:"):].strip()
#                 elif line.startswith("data:"):
#                     data = line[len("data:"):].strip()
#                     try:
#                         event["data"] = json.loads(data)
#                     except json.JSONDecodeError as e:
#                         logging.error(f"Failed to decode JSON: {e}, line: {line}")
#                 else:
#                     logging.warning(f"Unexpected line in SSE stream: {line}")
#
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
