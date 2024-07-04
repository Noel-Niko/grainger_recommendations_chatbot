import asyncio
import io
import logging
import os
import time
import streamlit as st
from PIL import Image
from faiss import IndexFlatL2
from langchain_aws import Bedrock
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from vector_index.document import initialize_embeddings_and_faiss
# from vector_index.utils import bedrock
from web_extraction_tools.product_reviews.call_selenium_for_review_async import async_navigate_to_reviews_selenium
from image_utils.grainger_image_util import main as generate_grainger_thumbnails, get_images
# from vector_index import Document as vectorIndexDocument
from vector_index.chat_processor import process_chat_question_with_customer_attribute_identifier
from langchain.embeddings import BedrockEmbeddings
from langchain.vectorstores import FAISS
from vector_index.bedrock_initializer import bedrock
import pandas as pd
import numpy as np


class StreamlitInterface:
    def __init__(self, index_document, LLM, bedrock_titan_embeddings, data_frame_singleton):
        self.document = index_document
        self.llm = LLM
        self.bedrock_embeddings = bedrock_titan_embeddings
        self.chat_history = []
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
            message, response_json, time_taken, customer_attributes_retrieved = self.process_chat_question(
                question=question, clear_history=False)

            products = response_json.get('products', [])
            logging.info(f"Products: {products}")

            center_col.subheader("Response:")
            time_to_initially_respond = time.time() - start_time
            center_col.write(f"Time taken to generate response: {time_to_initially_respond}")
            center_col.write(message)

            center_col.write(f"Time taken to generate customer attributes: {time_taken}")
            center_col.write(f"Customer attributes identified: {customer_attributes_retrieved}")

            await asyncio.gather(
                self.display_grainger_images(col3, products),
                self.display_reviews(products)
            )
            total_time = time.time() - start_time
            center_col.write(f"Total time to answer: {total_time}")


    def process_chat_question(self, question, clear_history=False):
        message, response_json, total_time, customer_attributes_retrieved = process_chat_question_with_customer_attribute_identifier(
            question,
            self.document,
            self.llm,
            self.chat_history,
            clear_history)
        return message, response_json, total_time, customer_attributes_retrieved

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
        recommendations_list = [f"{product['product']}, {product['code']}" for product in products]

        reviews_data = await async_navigate_to_reviews_selenium(recommendations_list[0], self.driver)
        if reviews_data:
            st.subheader('Extracted Reviews:')
            st.write(f"Average Star Rating: {reviews_data['Average Star Rating']}")
            st.write(f"Average Recommendation Percent: {reviews_data['Average Recommendation Percent']}")
            st.write("Review Texts:")
            for idx, review_text in enumerate(reviews_data['Review Texts'], start=1):
                st.write(f"\nReview {idx}: {review_text}")
        else:
            st.write("No reviews found for the given Product ID(s).")

        end_time_col1 = time.time()
        total_time_col1 = end_time_col1 - start_time_col1
        st.write(f"Time searching for reviews: {total_time_col1}")

        return reviews_data


def main():
    # df = Document.get_data_frame()  # Replace with your data retrieval method
    bedrock_embeddings, vectorstore_faiss_doc, df, llm = initialize_embeddings_and_faiss()

    interface = StreamlitInterface(index_document=vectorstore_faiss_doc, LLM=llm, bedrock_titan_embeddings=bedrock_embeddings,
                                   data_frame_singleton=df)
    interface.run()


if __name__ == "__main__":
    main()
