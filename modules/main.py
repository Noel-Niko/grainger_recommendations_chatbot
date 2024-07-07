import asyncio
import io
import logging
import time

import streamlit as st
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from image_utils.grainger_image_util import get_images
from vector_index.chat_processor import process_chat_question_with_customer_attribute_identifier
from vector_index.document import initialize_embeddings_and_faiss, parallel_search

from web_extraction_tools.product_reviews.call_selenium_for_review_async import async_navigate_to_reviews_selenium

class StreamlitInterface:
    def __init__(self, index_document, LLM, bedrock_titan_embeddings, data_frame_singleton):
        self.document = index_document
        self.llm = LLM
        self.bedrock_embeddings = bedrock_titan_embeddings
        self.df = data_frame_singleton
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--disable-gpu")
        self.service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=self.service, options=self.options)

    def run(self):
        st.set_page_config(layout="wide")
        st.title("Grainger Recommendations Chatbot")

        main_column, side_column = st.columns([2, 1])

        with main_column:
            asyncio.run(self.ask_question(main_column, side_column))

    async def ask_question(self, center_col, col3):
        question = st.text_input("Enter your question:", value="", placeholder="", key="unique_key_for_question")
        start_time = time.time()
        if question:
            # Await the async method properly
            message, response_json, time_taken, customer_attributes_retrieved = await self.process_chat_question(
                question=question, clear_history=False)

            products = response_json.get('products', [])
            logging.info(f"Products: {products}")

            center_col.subheader("Response:")
            time_to_initially_respond = time.time() - start_time
            center_col.write(f"Time taken to generate response: {time_to_initially_respond}")
            center_col.write(message)

            center_col.write(f"Time taken to generate customer attributes: {time_taken}")
            center_col.write(f"Customer attributes identified: {customer_attributes_retrieved}")

            # Use asyncio.gather to await multiple async functions
            await asyncio.gather(
                self.display_grainger_images(col3, products),
                self.display_reviews(products)
            )
            total_time = time.time() - start_time
            center_col.write(f"Total time to answer: {total_time}")

    async def process_chat_question(self, question, clear_history=False):
        start_time = time.time()

        # Run chat processing asynchronously
        message, response_json, customer_attributes_retrieved = await self.run_chat_processing(question, clear_history)

        # # Run FAISS search asynchronously
        # faiss_results = await self.run_faiss_search(response_json)

        time_taken = time.time() - start_time

        return message, response_json, time_taken, customer_attributes_retrieved

    async def run_chat_processing(self, question, clear_history):
        try:
            # Clear history if needed
            if clear_history:
                logging.info("Clearing chat history")
                st.session_state.chat_history.clear()

            logging.info(f"Initial chat history: {st.session_state.chat_history}")
            # Process chat question and retrieve response JSON
            message, response_json, total_time, customer_attributes_retrieved = process_chat_question_with_customer_attribute_identifier(
                question,
                self.document,
                self.llm,
                st.session_state.chat_history
            )

            # Append chat history with the current question
            st.session_state.chat_history.append([f"QUESTION: {question}. MESSAGE: {message}"])
            logging.info(f"Chat History in Main now: {st.session_state.chat_history}")
            return message, response_json, customer_attributes_retrieved

        except Exception as e:
            logging.error(f"Error in chat processing: {e}")
            return None, None, None

    async def display_grainger_images(self, col3, products):
        start_time_col3 = time.time()

        recommendations_list = [f"{product['product']}, {product['code']}" for product in products]

        image_data, total_image_time = await get_images(recommendations_list, self.df)

        for image_info in image_data:
            try:
                img = Image.open(io.BytesIO(image_info["Image Data"]))
                col3.image(img, caption=f"Grainger Product Image ({image_info['Code']})", use_column_width=True)
            except Exception as e:
                logging.error(f"Error displaying image: {e}")

        total_time_col3 = time.time() - start_time_col3
        col3.write(f"Time fetching images: {total_time_col3}")

    async def display_reviews(self, products):
        start_time_col1 = time.time()
        logging.info("Entering display_reviews method")

        try:
            st.subheader('Extracted Reviews:')
            for product in products:
                product_info = f"{product['product']}, {product['code']}"
                reviews_data = await async_navigate_to_reviews_selenium(product_info, self.driver)

                if reviews_data:
                    st.write(f"Product ID: {product['code']}")
                    st.write(f"Average Star Rating: {reviews_data['Average Star Rating']}")
                    st.write(f"Average Recommendation Percent: {reviews_data['Average Recommendation Percent']}")
                    st.write("Review Texts:")
                    for idx, review_text in enumerate(reviews_data['Review Texts'], start=1):
                        st.write(f"\nReview {idx}: {review_text}")
                else:
                    st.write(f"No reviews found for Product ID: {product['code']}")

        except Exception as e:
            logging.error(f"Error displaying reviews: {e}")
            st.write("Error fetching reviews.")

        end_time_col1 = time.time()
        total_time_col1 = end_time_col1 - start_time_col1
        st.write(f"Total time searching for reviews: {total_time_col1} seconds")

    # Health Check Endpoint
    async def health_check_endpoint(self):
        return "healthy"

def main():
    # Initialize chat_history in session_state if it doesn't exist
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    if 'vectorstore_faiss_doc' not in st.session_state or 'bedrock_embeddings' not in st.session_state or 'llm' not in st.session_state:
        logging.info("Generating session state variables...")
        bedrock_embeddings, vectorstore_faiss_doc, df, llm = initialize_embeddings_and_faiss()
        st.session_state.vectorstore_faiss_doc = vectorstore_faiss_doc
        st.session_state.bedrock_embeddings = bedrock_embeddings
        st.session_state.df = df
        st.session_state.llm = llm
        interface = StreamlitInterface(index_document=vectorstore_faiss_doc, LLM=llm,
                                   bedrock_titan_embeddings=bedrock_embeddings,
                                   data_frame_singleton=df)
        interface.run()
    else:
        logging.info("Using session state variables...")
        interface = StreamlitInterface(index_document=st.session_state.vectorstore_faiss_doc,
                                   LLM=st.session_state.llm,
                                   bedrock_titan_embeddings=st.session_state.bedrock_embeddings,
                                   data_frame_singleton=st.session_state.df)
        interface.run()

if __name__ == "__main__":
    main()
