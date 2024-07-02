import asyncio
import logging
import time
import streamlit as st

from image_utils.grainger_image_util import main as generate_grainger_thumbnails
from image_utils.ai_image_utils import main as generate_ai_thumbnails
from vector_index import Document as vectorIndexDocument
from vector_index.chat_processor import process_chat_question_with_customer_attribute_identifier


class StreamlitInterface:
    def __init__(self, index_document, LLM, bedrock_titan_embeddings):
        self.document = index_document
        self.llm = LLM
        self.bedrock_embeddings = bedrock_titan_embeddings
        self.chat_history = []

    def run(self):
        st.title("Ask a Question")

        # Create three columns with the center column twice as wide as the others
        col1, center_col, col3 = st.columns([1, 2, 1])

        with center_col:
            start_time_center = time.time()
            asyncio.run(self.ask_question(center_col, col1, col3))
            total_time_center = time.time() - start_time_center
            st.write(f"Time to render Center Column: {total_time_center}")

    async def ask_question(self, center_col, col1, col3):
        question = st.text_input("Enter your question:", value="", placeholder="")
        start_time = time.time()
        if question:
            message, response_json, time_taken = self.process_chat_question(question=question, clear_history=False)

            # Extract products from the response JSON
            products = response_json.get('products', [])
            logging.info(f"Products: {products}")

            # # Start rendering col1 images asynchronously
            # task_col1 = asyncio.create_task(self.display_ai_images(col1, products))

            center_col.write(f"Response: {message}")
            center_col.write(f"Time taken: {time_taken}")

            # Render col3 images without waiting for col1
            await self.display_grainger_images(col3, products)

            # Wait for col1 images to finish rendering
            # await task_col1

            # Display the total time for ask_question
            total_time = time.time() - start_time
            center_col.write(f"Total time for ask_question: {total_time}")

    def process_chat_question(self, question, clear_history=False):
        message, response_json, total_time = process_chat_question_with_customer_attribute_identifier(question, self.document,
                                                                                          self.llm, self.chat_history,
                                                                                          clear_history)
        return message, response_json, total_time

    async def display_ai_images(self, col1, products):
        start_time_col1 = time.time()
        col1.header("AI Images")

        image_strips_col1 = await generate_ai_thumbnails(col1, products, self.bedrock_embeddings)

        # Display the HTML table with all thumbnails in col1
        col1.markdown("".join(image_strips_col1), unsafe_allow_html=True)

        end_time_col1 = time.time()
        total_time_col1 = end_time_col1 - start_time_col1
        col1.write(f"Time to render AI Images for col1: {total_time_col1}")

    async def display_grainger_images(self, col3, products):
        start_time_col3 = time.time()
        col3.header("Grainger Images")

        # Extract image URLs from products
        image_url_maps = [product['product']['Image URL'] for product in products if
                          'product' in product and 'Image URL' in product['product']]

        # Generate thumbnails and HTML content for col3 using grainger_image_util
        html_content, total_time = await generate_grainger_thumbnails(image_url_maps, self.document)

        # Debugging statement
        col3.write(f"HTML Content: {html_content}")


        # Display the HTML content in col3
        col3.markdown(html_content, unsafe_allow_html=True)

        end_time_col3 = time.time()
        total_time2 = end_time_col3 - start_time_col3
        col3.write(f"Time to render: {total_time2}")


if __name__ == "__main__":
    document, llm, bedrock_embeddings = vectorIndexDocument.get_instance()
    interface = StreamlitInterface(index_document=document, LLM=llm, bedrock_titan_embeddings=bedrock_embeddings)
    interface.run()

# import asyncio
# import time
# import streamlit as st
#
# from image_utils.grainger_image_util import main as generate_grainger_thumbnails
# from image_utils.ai_image_utils import main as generate_ai_thumbnails
# from vector_index import Document as vectorIndexDocument
# from vector_index.chat_processor import process_chat_question_with_customer_attribute_identifier
#
#
# class StreamlitInterface:
#     def __init__(self, index_document, LLM, bedrock_titan_embeddings):
#         self.document = index_document
#         self.llm = LLM
#         self.bedrock_embeddings = bedrock_titan_embeddings
#         self.chat_history = []
#
#     def run(self):
#         st.title("Ask a Question")
#
#         # Create three columns with the center column twice as wide as the others
#         col1, center_col, col3 = st.columns([1, 2, 1])
#
#         with center_col:
#             start_time_center = time.time()
#             asyncio.run(self.ask_question(center_col, col1, col3))
#             total_time_center = time.time() - start_time_center
#             st.write(f"Time to render Center Column: {total_time_center}")
#
#     async def ask_question(self, center_col, col1, col3):
#         question = st.text_input("Enter your question:", value="", placeholder="")
#         start_time = time.time()
#         if question:
#             message, products, time_taken = self.process_chat_question(question=question, clear_history=False)
#
#             # # Start rendering col1 images asynchronously
#             # task_col1 = asyncio.create_task(self.display_ai_images(col1, products))
#
#             center_col.write(f"Response: {message}")
#             center_col.write(f"Time taken: {time_taken}")
#
#             # Render col3 images without waiting for col1
#             await self.display_grainger_images(col3, products)
#
#             # Wait for col1 images to finish rendering
#             # await task_col1
#
#             # Display the total time for ask_question
#             total_time = time.time() - start_time
#             center_col.write(f"Total time for ask_question: {total_time}")
#
#     def process_chat_question(self, question, clear_history=False):
#         return process_chat_question_with_customer_attribute_identifier(question, self.document, self.llm,
#                                                                         self.chat_history, clear_history)
#
#     async def display_ai_images(self, col1, products):
#         start_time_col1 = time.time()
#         col1.header("AI Images")
#
#         image_strips_col1 = await generate_ai_thumbnails(col1, products, self.bedrock_embeddings)
#
#         # Display the HTML table with all thumbnails in col1
#         col1.markdown("".join(image_strips_col1), unsafe_allow_html=True)
#
#         end_time_col1 = time.time()
#         total_time_col1 = end_time_col1 - start_time_col1
#         col1.write(f"Time to render AI Images for col1: {total_time_col1}")
#
#     async def display_grainger_images(self, col3, products):
#         start_time_col3 = time.time()
#         col3.header("Grainger Images")
#
#         # Extract image URLs from products
#         image_url_maps = [product['Image URL'] for product in products]
#
#         # Generate thumbnails and HTML content for col3 using grainger_image_util
#         html_content, total_time = await generate_grainger_thumbnails(image_url_maps, self.document)
#
#         # Display the HTML content in col3
#         col3.markdown(html_content, unsafe_allow_html=True)
#
#         end_time_col3 = time.time()
#         total_time2 = end_time_col3 - start_time_col3
#         col3.write(f"Time to render Grainger Images for col3: {total_time2}")
#
#
# if __name__ == "__main__":
#     document, llm, bedrock_embeddings = vectorIndexDocument.get_instance()
#     interface = StreamlitInterface(index_document=document, LLM=llm, bedrock_titan_embeddings=bedrock_embeddings)
#     interface.run()

# import asyncio
# import time
# import streamlit as st
#
# from image_utils.grainger_image_util import main as generate_grainger_thumbnails
# from image_utils.ai_image_utils import main as generate_ai_thumbnails
# from vector_index import Document as vectorIndexDocument
# from vector_index.chat_processor import process_chat_question_with_customer_attribute_identifier
#
#
# class StreamlitInterface:
#     def __init__(self, index_document, LLM, bedrock_titan_embeddings):
#         self.document = index_document
#         self.llm = LLM
#         self.bedrock_embeddings = bedrock_titan_embeddings
#         self.chat_history = []
#
#     def run(self):
#         st.title("Ask a Question")
#
#         # Create three columns with the center column twice as wide as the others
#         col1, center_col, col3 = st.columns([1, 2, 1])
#
#         with center_col:
#             start_time_center = time.time()
#             asyncio.run(self.ask_question(center_col, col1, col3))
#             total_time_center = time.time() - start_time_center
#             st.write("Time to render Center Column:", total_time_center)
#
#     async def ask_question(self, center_col, col1, col3):
#         question = st.text_input("Enter your question:", value="", placeholder="")
#         start_time = time.time()
#         if question:
#             message, products, time_taken = self.process_chat_question(question=question, clear_history=False)
#
#             # # Start rendering col1 images asynchronously
#             # task_col1 = asyncio.create_task(self.display_ai_images(col1, products))
#
#             center_col.write(f"Response: {message}")
#             center_col.write("Time taken:", time_taken)
#
#             # Render col3 images without waiting for col1
#             await self.display_grainger_images(col3, products)
#
#             # Wait for col1 images to finish rendering
#             await task_col1
#
#             # Display the total time for ask_question
#             total_time = time.time() - start_time
#             center_col.write(f"Total time for ask_question: {total_time}")
#
#
#     def process_chat_question(self, question, clear_history=False):
#         return process_chat_question_with_customer_attribute_identifier(question, self.document, self.llm, self.chat_history, clear_history)
#
#     async def display_ai_images(self, col1, products):
#         start_time_col1 = time.time()
#         st.header("AI Images")
#
#         image_strips_col1 = await generate_ai_thumbnails(col1, products, self.bedrock_embeddings)
#
#         # Display the HTML table with all thumbnails in col1
#         st.markdown("".join(image_strips_col1), unsafe_allow_html=True)
#
#         end_time_col1 = time.time()
#         total_time_col1 = end_time_col1 - start_time_col1
#         st.write(f"Time to render AI Images for col1: {total_time_col1}")
#
#     async def display_grainger_images(self, col3, products):
#         start_time_col3 = time.time()
#         st.header("Grainger Images")
#
#         # Extract image URLs from products
#         image_url_maps = [product['Image URL'] for product, _ in products]
#
#         # Generate thumbnails and HTML content for col3 using grainger_image_util
#         html_content, total_time = await generate_grainger_thumbnails(image_url_maps, self.document)
#
#         # Display the HTML content in col3
#         col3.markdown(html_content, unsafe_allow_html=True)
#
#         end_time_col3 = time.time()
#         total_time2 = end_time_col3 - start_time_col3
#         st.write("Time to render Grainger Images for col3:", total_time2)
#
#
# if __name__ == "__main__":
#     document, llm, bedrock_embeddings = vectorIndexDocument.get_instance()
#     interface = StreamlitInterface(index_document=document, LLM=llm, bedrock_titan_embeddings=bedrock_embeddings)
#     interface.run()
#
#




# import asyncio
# import time
# import streamlit as st
#
# from image_utils.grainger_image_util import main  # Adjust import path as per your directory structure
# from modules.image_utils.ai_image_utils import generate_ai_thumbnail
# from vector_index import Document as vectorIndexDocument
# from vector_index.chat_processor import process_chat_question
#
#
# class StreamlitInterface:
#     def __init__(self, index_document, LLM, bedrock_titan_embeddings):
#         self.document = index_document
#         self.llm = LLM
#         self.bedrock_embeddings = bedrock_titan_embeddings
#         self.chat_history = []
#
#     def run(self):
#         st.title("Ask a Question")
#
#         # Create three columns with the center column twice as wide as the others
#         col1, center_col, col3 = st.columns([1, 2, 1])
#
#         with center_col:
#             start_time_center = time.time()
#             asyncio.run(self.ask_question(center_col, col1, col3))
#             end_time_center = time.time()
#             st.write("Time to render Center Column:", end_time_center - start_time_center)
#
#     async def ask_question(self, center_col, col1, col3):
#         question = st.text_input("Enter your question:", value="", placeholder="")
#         start_time = time.time()
#         if question:
#             response, products, time_taken = self.process_chat_question(question=question, clear_history=False)
#             await self.display_images(col1, products, col3)  # Pass col3 to display_images
#
#             center_col.write("Response:", response)
#             center_col.write("Time taken:", time_taken)
#
#         end_time = time.time()
#         center_col.write("Total time for ask_question:", end_time - start_time)
#
#     def process_chat_question(self, question, clear_history=False):
#         return process_chat_question(question, self.document, self.llm, self.chat_history, clear_history)
#
#     async def display_images(self, col1, products, col3):
#         start_time_col1 = time.time()
#         st.header("Images")
#
#         # Assuming 'products' is a list of tuples (rec, attributes) required by generate_thumbnail
#         image_elements_col1 = [generate_ai_thumbnail(product, attributes) for product, attributes in products]
#
#         # Wait for all thumbnails to be generated for col1
#         image_strips_col1 = await asyncio.gather(*image_elements_col1)
#
#         # Display the HTML table with all thumbnails in col1
#         st.markdown("".join(image_strips_col1), unsafe_allow_html=True)
#
#         end_time_col1 = time.time()
#         st.write("Time to render Images for col1:", end_time_col1 - start_time_col1)
#
#         # Generate thumbnails and HTML content for col3 using grainger_image_util
#         image_url_maps = [product['Image URL'] for product, _ in products]
#         html_content, total_time = await main(image_url_maps, self.document)  # Adjust parameters as per your setup
#         col3.markdown(html_content, unsafe_allow_html=True)
#
#         end_time_col3 = time.time()
#         st.write("Time to render Images for col3:", end_time_col3 - end_time_col1)  # Time for col3
#
# if __name__ == "__main__":
#     document, llm, bedrock_embeddings = vectorIndexDocument.get_instance()
#     interface = StreamlitInterface(index_document=document, LLM=llm, bedrock_titan_embeddings=bedrock_embeddings)
#     interface.run()
#


# import asyncio
# import time
# import streamlit as st
#
# from modules.image_utils.ai_image_utils import generate_thumbnail
# from vector_index import Document as vectorIndexDocument
# from vector_index.chat_processor import process_chat_question
#
#
# class StreamlitInterface:
#     def __init__(self, index_document, LLM, bedrock_titan_embeddings):
#         self.document = index_document
#         self.llm = LLM
#         self.bedrock_embeddings = bedrock_titan_embeddings
#         self.chat_history = []
#
#     def run(self):
#         st.title("Ask a Question")
#
#         # Create three columns with the center column twice as wide as the others
#         col1, center_col, col3 = st.columns([1, 2, 1])
#
#         with center_col:
#             start_time_center = time.time()
#             asyncio.run(self.ask_question(center_col, col1, col3))
#             end_time_center = time.time()
#             st.write("Time to render Center Column:", end_time_center - start_time_center)
#
#     async def ask_question(self, center_col, col1, col3):
#         question = st.text_input("Enter your question:", value="", placeholder="")
#         start_time = time.time()
#         if question:
#             response, products, time_taken = self.process_chat_question(question=question, clear_history=False)
#             await self.display_images(col1, products)  # Await here
#
#             center_col.write("Response:", response)
#             center_col.write("Time taken:", time_taken)
#
#         end_time = time.time()
#         center_col.write("Total time for ask_question:", end_time - start_time)
#
#     def process_chat_question(self, question, clear_history=False):
#         return process_chat_question(question, self.document, self.llm, self.chat_history, clear_history)
#
#     async def display_images(self, col1, products):
#         start_time_col1 = time.time()
#         st.header("Images")
#
#         # Assuming 'products' is a list of tuples (rec, attributes) required by generate_thumbnail
#         image_elements = [generate_thumbnail(product, attributes) for product, attributes in products]
#
#         # Wait for all thumbnails to be generated
#         image_strips = await asyncio.gather(*image_elements)
#
#         # Display the HTML table with all thumbnails
#         st.markdown("".join(image_strips), unsafe_allow_html=True)
#
#         end_time_col1 = time.time()
#         st.write("Time to render Images:", end_time_col1 - start_time_col1)
#
#
# if __name__ == "__main__":
#     document, llm, bedrock_embeddings = vectorIndexDocument.get_instance()
#     interface = StreamlitInterface(index_document=document, LLM=llm, bedrock_titan_embeddings=bedrock_embeddings)
#     interface.run()

# import asyncio
# import time
# import streamlit as st
#
# from modules.image_utils.image_utils import generate_thumbnail
# from vector_index import Document as vectorIndexDocument
# from vector_index.chat_processor import process_chat_question
#
# class StreamlitInterface:
#     def __init__(self, index_document, LLM, bedrock_titan_embeddings):
#         self.document = index_document
#         self.llm = LLM
#         self.bedrock_embeddings = bedrock_titan_embeddings
#         self.chat_history = []
#
#     def run(self):
#         st.title("Ask a Question")
#
#         # Create three columns with the center column twice as wide as the others
#         col1, center_col, col3 = st.columns([1, 2, 1])
#
#         with center_col:
#             start_time_center = time.time()
#             asyncio.run(self.ask_question(center_col, col1, col3))
#             end_time_center = time.time()
#             st.write("Time to render Center Column:", end_time_center - start_time_center)
#
#     async def ask_question(self, center_col, col1, col3):
#         question = st.text_input("Enter your question:", value="", placeholder="")
#         start_time = time.time()
#         if question:
#             response, products, time_taken = self.process_chat_question(question=question, clear_history=False)
#             await self.display_images(col1, products)
#
#             center_col.write("Response:", response)
#             center_col.write("Time taken:", time_taken)
#
#         end_time = time.time()
#         center_col.write("Total time for ask_question:", end_time - start_time)
#
#     def process_chat_question(self, question, clear_history=False):
#         return process_chat_question(question, self.document, self.llm, self.chat_history, clear_history)
#
#     async def display_images(self, col1, products):
#         start_time_col1 = time.time()
#         st.header("Images")
#
#         # Assuming 'products' is a list of tuples (rec, attributes) required by generate_thumbnail
#         image_elements = [generate_thumbnail(product, attributes) for product, attributes in products]
#
#         # Wait for all thumbnails to be generated
#         image_strips = await asyncio.gather(*image_elements)
#
#         # Display the HTML table with all thumbnails
#         st.markdown("".join(image_strips), unsafe_allow_html=True)
#
#         end_time_col1 = time.time()
#         st.write("Time to render Images:", end_time_col1 - start_time_col1)
#
#
# if __name__ == "__main__":
#     document, llm, bedrock_embeddings = vectorIndexDocument.get_instance()
#     interface = StreamlitInterface(index_document=document, LLM=llm, bedrock_titan_embeddings=bedrock_embeddings)

# import time
#
# import streamlit as st
#
# from vector_index import Document as vectorIndexDocument
# from vector_index.chat_processor import process_chat_question
#
#
# class StreamlitInterface:
#     def __init__(self, index_document, LLM, bedrock_titan_embeddings):
#         self.document = index_document
#         self.llm = LLM
#         self.bedrock_embeddings = bedrock_titan_embeddings
#         self.chat_history = []
#
#     def ask_question(self):
#         question = st.text_input("Enter your question:", value="", placeholder="")
#         start_time = time.time()
#         if question:
#             response, products, time_taken = self.process_chat_question(question=question, clear_history=False)
#             st.write("Response:", response)
#             st.write("Time taken:", time_taken)
#         end_time = time.time()
#         st.write("Total time for ask_question:", end_time - start_time)
#
#     def process_chat_question(self, question, clear_history=False):
#         return process_chat_question(question, self.document, self.llm, self.chat_history, clear_history)
#
#     def run(self):
#         start_time = time.time()
#         st.title("Ask a Question")
#         self.ask_question()
#         end_time = time.time()
#         st.write("Total time for run:", end_time - start_time)
#
#
# if __name__ == "__main__":
#     document, llm, bedrock_embeddings = vectorIndexDocument.get_instance()
#     interface = StreamlitInterface(index_document=document, LLM=llm, bedrock_titan_embeddings=bedrock_embeddings)
#     interface.run()
