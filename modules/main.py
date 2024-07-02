import asyncio
import io
import logging
import time
import os
import base64
import tempfile
from PIL import Image
import streamlit as st

from image_utils.grainger_image_util import main as generate_grainger_thumbnails, get_images
from image_utils.ai_image_utils import main as generate_ai_thumbnails
from vector_index import Document as vectorIndexDocument
from vector_index.chat_processor import process_chat_question_with_customer_attribute_identifier


class StreamlitInterface:
    def __init__(self, index_document, LLM, bedrock_titan_embeddings, data_frame_singleton):
        self.document = index_document
        self.llm = LLM
        self.bedrock_embeddings = bedrock_titan_embeddings
        self.chat_history = []
        self.df = data_frame_singleton

    def run(self):
        st.title("Grainger Recommendations Chatbot")

        main_column, side_column = st.columns([2, 1])

        with main_column:
            asyncio.run(self.ask_question(main_column, side_column))


    async def ask_question(self, center_col, col3):
        question = st.text_input("Enter your question:", value="", placeholder="")
        start_time = time.time()
        if question:
            message, response_json, time_taken, customer_attributes_retrieved = self.process_chat_question(question=question, clear_history=False)

            products = response_json.get('products', [])
            logging.info(f"Products: {products}")

            center_col.write(f"Response: {message}")
            center_col.write(f"Time taken: {time_taken}")
            center_col.write(f"Customer attributes identified: {customer_attributes_retrieved}")

            await self.display_grainger_images(col3, products)

            total_time = time.time() - start_time
            center_col.write(f"Total time to answer: {total_time}")

            await self.display_reviews(products)

    def process_chat_question(self, question, clear_history=False):
        message, response_json, total_time, customer_attributes_retrieved = process_chat_question_with_customer_attribute_identifier(question,
                                                                                                      self.document,
                                                                                                      self.llm,
                                                                                                      self.chat_history,
                                                                                                      clear_history)
        return message, response_json, total_time, customer_attributes_retrieved

    async def display_reviews(self, products):
        start_time_col1 = time.time()


        recommendations_list = [f"{product['product']}, {product['code']}" for product in products]

        end_time_col1 = time.time()
        total_time_col1 = end_time_col1 - start_time_col1
        st.write(f"Time searching for reviews: {total_time_col1}")

    async def display_grainger_images(self, col3, products):
        start_time_col3 = time.time()
        # col3.header("Grainger Images")

        recommendations_list = [f"{product['product']}, {product['code']}" for product in products]

        image_data, total_image_time = await get_images(recommendations_list, self.df)

        for image_info in image_data:
            try:
                img = Image.open(io.BytesIO(image_info["Image Data"]))
                col3.image(img, caption=f"Grainger Product Image ({image_info['Code']})", use_column_width=True)
            except Exception as e:
                logging.error(f"Error loading image {image_info['Code']}: {str(e)}")
                col3.write(f"Error loading image {image_info['Code']}")

        end_time_col3 = time.time()
        total_time2 = end_time_col3 - start_time_col3
        col3.write(f"Time to extract image url's: {total_image_time}")
        col3.write(f"Time to render: {total_time2}")

    def display_base64_image(self, base64_img_str):
        decoded_img_data = base64.b64decode(base64_img_str)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            temp_file.write(decoded_img_data)
            temp_file_path = temp_file.name

        img = Image.open(temp_file_path)
        st.image(img, caption="Grainger Product Image", use_column_width=True)

        os.unlink(temp_file_path)


if __name__ == "__main__":
    document, llm, bedrock_embeddings, df = vectorIndexDocument.get_instance()
    interface = StreamlitInterface(index_document=document, LLM=llm, bedrock_titan_embeddings=bedrock_embeddings,
                                   data_frame_singleton=df)
    interface.run()
