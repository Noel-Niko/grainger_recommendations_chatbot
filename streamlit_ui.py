import asyncio
import io
import logging
import time
import requests
import streamlit as st
from PIL import Image

tag = "StreamlitInterface"
class StreamlitInterface:
    def __init__(self):
        self.session_id = None

    def initialize_session(self):
        response = requests.get("http://localhost:8000/initialize_session")
        if response.status_code == 200:
            self.session_id = response.json().get("session_id")
            logging.info(f"{tag}/Initialized session with ID: {self.session_id}")
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
            asyncio.run(self.ask_question(main_column, side_column))

    def clear_chat_history(self):
        st.session_state.chat_history = []

    async def ask_question(self, center_col, col3):
        logging.info("Asking question")
        question = st.text_input("Enter your question:", value="", placeholder="", key="unique_key_for_question")
        if question:
            start_time = time.time()
            logging.info(f"Question entered: {question}")

            # Call FastAPI to process the chat question
            headers = {"session-id": self.session_id}
            payload = {"question": question, "clear_history": False}
            response = requests.post("http://localhost:8000/ask_question", json=payload, headers=headers)

            if response.status_code == 200:
                data = response.json()
                message = data["message"]
                response_json = data["response_json"]
                customer_attributes_retrieved = data["customer_attributes_retrieved"]
                time_to_get_attributes = data["time_to_get_attributes"]
            else:
                logging.error(f"Failed to process chat question: {response.text}")
                message = response_json = customer_attributes_retrieved = time_to_get_attributes = None

            time_taken = time.time() - start_time

            # Ensure response_json is not None before accessing its attributes
            if response_json is not None:
                products = response_json.get('products', [])
                logging.info(f"Products: {products}")

                center_col.subheader("Response:")
                time_to_initially_respond = time.time() - start_time
                center_col.write(f"Time taken to generate response: {time_to_initially_respond}")
                center_col.write(message)

                center_col.write(f"Time taken to generate customer attributes: {time_to_get_attributes}")
                center_col.write(f"Customer attributes identified in last question: {customer_attributes_retrieved}")

                await asyncio.gather(
                    self.display_grainger_images(col3, products),
                    # self.display_reviews(products)
                )
                total_time = time.time() - start_time
                center_col.write(f"Total time to answer: {total_time}")
            else:
                logging.error("Received None response_json from FastAPI")

    async def process_chat_question(self, question, clear_history=False):
        start_time = time.time()

        # Run chat processing asynchronously
        headers = {"session-id": self.session_id}
        payload = {"question": question, "clear_history": clear_history}
        response = await asyncio.to_thread(requests.post, "http://localhost:8000/ask_question", json=payload, headers=headers)
        logging.info(f"{tag}/Response code: {response.status_code}")
        logging.info(f"{tag}/Response Json: {response.text}")
        if response.status_code == 200:
            data = response.json()
            message = data["message"]
            response_json = data["response_json"]
            customer_attributes_retrieved = data["customer_attributes_retrieved"]
            time_to_get_attributes = data["time_to_get_attributes"]
        else:
            logging.error(f"Failed to process chat question: {response.text}")
            message = response_json = customer_attributes_retrieved = time_to_get_attributes = None

        time_taken = time.time() - start_time

        return message, response_json, time_taken, customer_attributes_retrieved, time_to_get_attributes

    async def display_grainger_images(self, col3, products):
        start_time_col3 = time.time()

        recommendations_list = [f"{product['product']}, {product['code']}" for product in products]

        image_data = await self.fetch_images(recommendations_list)

        for image_info in image_data:
            try:
                img = Image.open(io.BytesIO(image_info["image_data"]))
                col3.image(img, caption=f"Grainger Product Image ({image_info['code']})", use_column_width=True)
            except Exception as e:
                logging.error(f"Error displaying image: {e}")

        total_time_col3 = time.time() - start_time_col3
        col3.write(f"Time fetching images: {total_time_col3}")

    async def fetch_images(self, recommendations_list):
        response = await asyncio.to_thread(requests.post, "http://localhost:8000/fetch_images", json={"products": recommendations_list})
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Failed to fetch images: {response.text}")
            return []

def main():
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    interface = StreamlitInterface()
    interface.run()

if __name__ == "__main__":
    main()


























# import asyncio
# import io
# import logging
# import time
# import requests
# import streamlit as st
# from PIL import Image
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
#
# from modules.image_utils.grainger_image_util import get_images
# from modules.vector_index.chat_processor import process_chat_question_with_customer_attribute_identifier
# from modules.vector_index.document import initialize_embeddings_and_faiss, parallel_search
#
# from modules.web_extraction_tools.product_reviews.call_selenium_for_review_async import async_navigate_to_reviews_selenium
#
#
# class StreamlitInterface:
#     def __init__(self, index_document, LLM, bedrock_titan_embeddings, data_frame_singleton):
#         self.document = index_document
#         self.llm = LLM
#         self.bedrock_embeddings = bedrock_titan_embeddings
#         self.df = data_frame_singleton
#         self.options = Options()
#         self.options.add_argument("--headless")
#         self.options.add_argument("--disable-gpu")
#         self.service = Service(ChromeDriverManager().install())
#         self.driver = webdriver.Chrome(service=self.service, options=self.options)
#         self.session_id = None
#
#     def initialize_session(self):
#         response = requests.get("http://localhost:8000/initialize_session")
#         if response.status_code == 200:
#             self.session_id = response.json().get("session_id")
#             logging.info(f"{tag}/Initialized session with ID: {self.session_id}")
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
#             asyncio.run(self.ask_question(main_column, side_column))
#
#     def clear_chat_history(self):
#         st.session_state.chat_history = []
#
#     async def ask_question(self, center_col, col3):
#         logging.info("Asking question")
#         question = st.text_input("Enter your question:", value="", placeholder="", key="unique_key_for_question")
#         if question:
#             start_time = time.time()
#             logging.info(f"{tag}/Question entered: {question}")
#             # Await the async method properly
#             message, response_json, time_taken, customer_attributes_retrieved, time_to_get_attributes = await self.process_chat_question(
#                 question=question, clear_history=False)
#
#             products = response_json.get('products', [])
#             logging.info(f"{tag}/Products: {products}")
#
#             center_col.subheader("Response:")
#             time_to_initially_respond = time.time() - start_time
#             center_col.write(f"Time taken to generate response: {time_to_initially_respond}")
#             center_col.write(message)
#
#             center_col.write(f"Time taken to generate customer attributes: {time_to_get_attributes}")
#             center_col.write(f"Customer attributes identified in last question: {customer_attributes_retrieved}")
#
#             # Use asyncio.gather to await multiple async functions
#             await asyncio.gather(
#                 self.display_grainger_images(col3, products),
#                 # self.display_reviews(products)
#             )
#             total_time = time.time() - start_time
#             center_col.write(f"Total time to answer: {total_time}")
#
#     async def process_chat_question(self, question, clear_history=False):
#         start_time = time.time()
#
#         # Run chat processing asynchronously
#         headers = {"session-id": self.session_id}
#         payload = {"question": question, "clear_history": clear_history}
#         response = requests.post("http://localhost:8000/ask_question", json=payload, headers=headers)
#
#         if response.status_code == 200:
#             data = response.json()
#             message = data["message"]
#             response_json = data["response_json"]
#             customer_attributes_retrieved = data["customer_attributes_retrieved"]
#             time_to_get_attributes = data["time_to_get_attributes"]
#         else:
#             logging.error(f"Failed to process chat question: {response.text}")
#             message = response_json = customer_attributes_retrieved = time_to_get_attributes = None
#
#         time_taken = time.time() - start_time
#
#         return message, response_json, time_taken, customer_attributes_retrieved, time_to_get_attributes
#
#     async def display_grainger_images(self, col3, products):
#         start_time_col3 = time.time()
#
#         recommendations_list = [f"{product['product']}, {product['code']}" for product in products]
#
#         image_data, total_image_time = await get_images(recommendations_list, self.df)
#
#         for image_info in image_data:
#             try:
#                 img = Image.open(io.BytesIO(image_info["Image Data"]))
#                 col3.image(img, caption=f"Grainger Product Image ({image_info['Code']})", use_column_width=True)
#             except Exception as e:
#                 logging.error(f"Error displaying image: {e}")
#
#         total_time_col3 = time.time() - start_time_col3
#         col3.write(f"Time fetching images: {total_time_col3}")
#
#     async def display_reviews(self, products):
#         start_time_col1 = time.time()
#         logging.info("Entering display_reviews method")
#
#         try:
#             st.subheader('Extracted Reviews:')
#             for product in products:
#                 product_info = f"{product['product']}, {product['code']}"
#                 reviews_data = await async_navigate_to_reviews_selenium(product_info, self.driver)
#
#                 if reviews_data:
#                     st.write(f"Product ID: {product['code']}")
#                     st.write(f"Average Star Rating: {reviews_data['Average Star Rating']}")
#                     st.write(f"Average Recommendation Percent: {reviews_data['Average Recommendation Percent']}")
#                     st.write("Review Texts:")
#                     for idx, review_text in enumerate(reviews_data['Review Texts'], start=1):
#                         st.write(f"\nReview {idx}: {review_text}")
#                 else:
#                     st.write(f"No reviews found for Product ID: {product['code']}")
#
#         except Exception as e:
#             logging.error(f"Error displaying reviews: {e}")
#             st.write("Error fetching reviews.")
#
#         end_time_col1 = time.time()
#         total_time_col1 = end_time_col1 - start_time_col1
#         st.write(f"Total time searching for reviews: {total_time_col1} seconds")
#
#
# def main():
#     # Initialize chat_history in session_state if it doesn't exist
#     if 'chat_history' not in st.session_state:
#         st.session_state.chat_history = []
#
#     if 'vectorstore_faiss_doc' not in st.session_state or 'bedrock_embeddings' not in st.session_state or 'llm' not in st.session_state:
#         logging.info("Generating session state variables...")
#         bedrock_embeddings, vectorstore_faiss_doc, df, llm = initialize_embeddings_and_faiss()
#         st.session_state.vectorstore_faiss_doc = vectorstore_faiss_doc
#         st.session_state.bedrock_embeddings = bedrock_embeddings
#         st.session_state.df = df
#         st.session_state.llm = llm
#         interface = StreamlitInterface(index_document=vectorstore_faiss_doc, LLM=llm,
#                                        bedrock_titan_embeddings=bedrock_embeddings,
#                                        data_frame_singleton=df)
#         interface.run()
#     else:
#         logging.info("Using session state variables...")
#         interface = StreamlitInterface(index_document=st.session_state.vectorstore_faiss_doc,
#                                        LLM=st.session_state.llm,
#                                        bedrock_titan_embeddings=st.session_state.bedrock_embeddings,
#                                        data_frame_singleton=st.session_state.df)
#         interface.run()
#
#
# if __name__ == "__main__":
#     main()
#
# # import logging
# # import sys
# # import uuid
# #
# # import streamlit as st
# # import requests
# #
# # st.title("Grainger Recommendations Chatbot")
# #
# # backend_url = "http://localhost:8000"
# #
# # # Initialize session
# # if 'session_id' not in st.session_state:
# #     st.session_state['session_id'] = str(uuid.uuid4())
# #     # response = requests.get(f"{backend_url}/initialize_session")
# #     # logging.info(f"{tag}/backend_url: {backend_url}")
# #     # logging.info(f"{tag}/session_id: {response.text}")
# #     # if response.status_code == 200:
# #     #     st.session_state.session_id = response.json().get("session_id")
# #
# # # Ask a question
# # question = st.text_input("Enter your question:")
# # if st.button("Ask"):
# #     logging.info(f"{tag}/Streamlit App pointing to {backend_url}")
# #     if st.session_state.session_id:
# #         response = requests.post(
# #             f"{backend_url}/ask_question",
# #             headers={"session-id": st.session_state.session_id},
# #             json={"question": question, "clear_history": False}
# #         )
# #         if response.status_code == 200:
# #             data = response.json()
# #             st.write("Response:", data["message"])
# #             st.write("Response JSON:", data["response_json"])
# #             st.write("Time taken:", data["time_taken"])
# #             st.write("Customer attributes retrieved:", data["customer_attributes_retrieved"])
# #             st.write("Time to get attributes:", data["time_to_get_attributes"])
# #         else:
# #             st.write("Error:", response.text)
# #
# # # Fetch images
# # st.write("Fetch Images")
# # product_info = st.text_area("Enter product info as JSON list (e.g. [{'product': 'Product1', 'code': '12345'}])")
# # if st.button("Fetch Images"):
# #     try:
# #         products = eval(product_info)
# #         response = requests.post(
# #             f"{backend_url}/fetch_images",
# #             json=products
# #         )
# #         if response.status_code == 200:
# #             image_data_list = response.json()
# #             for image_data in image_data_list:
# #                 st.image(image_data["image_data"], caption=image_data["code"])
# #         else:
# #             st.write("Error:", response.text)
# #     except Exception as e:
# #         st.write("Invalid JSON input:", str(e))
# #
# # # Fetch reviews
# # st.write("Fetch Reviews")
# # # review_info = st.text_area("Enter product info as JSON list (e.g. [{'product': 'Product1', 'code': '12345'}])")
# # # if st.button("Fetch Reviews"):
# # #     try:
# # #         products = eval(review_info)
# # #         response = requests.post(
# # #             f"{backend_url}/fetch_reviews",
# # #             json=products
# # #         )
# # #         if response.status_code == 200:
# # #             reviews = response.json()
# # #             st.write(reviews)
# # #         else:
# # #             st.write("Error:", response.text)
# # #     except Exception as e:
# # #         st.write("Invalid JSON input:", str(e))
