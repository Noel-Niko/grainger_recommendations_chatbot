# import time
# import re
# import json
# import numpy as np
# import streamlit as st
#
# from vector_index import Document as vectorIndexDocument
# from langchain.chains import RetrievalQA
# from langchain.prompts import PromptTemplate
# from langchain.chains.conversational_retrieval.prompts import QA_PROMPT
# from langchain.llms.bedrock import Bedrock
# from langchain.chains import LLMChain
#
# prompt_template2 = """Human: Extract list of 5 products and their respective physical IDs from catalog that answer the user question.
# The catalog of products is provided under <catalog></catalog> tags below.
# <catalog>
# {context}
# </catalog>
# Question: {question}
#
# The output should be a json of the form <products>[{{"product": <description of the product from the catalog>, "code":<code of the product from the catalog>}}, ...]</products>
# Skip the preamble and always return valid json.
# Assistant: """
# PROMPT = PromptTemplate(
#     template=prompt_template2, input_variables=["context", "question"]
# )
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
#     @staticmethod
#     def extract_customer_attributes(customer_input):
#         start_time = time.time()
#         # Define the NER prompt with placeholders for the customer input
#         ner_prompt = """Human: Find industry, size, Sustainability Focus, Inventory Manager, and the location in the customer input.
#         Instructions:
#         The industry can be one of the following: Manufacturing, Warehousing, Government and Public Safety, Education, Food and Beverage Distribution, Hospitality, Property Management, Retail, or Other
#         The size can be one of the following: Small Businesses (Smaller companies might prioritize cost-effective solutions and fast shipping options), or Large Enterprises (Larger organizations may require more comprehensive solutions, including strategic services like inventory management and safety consulting), Womens, Other
#         The Sustainability Focused true or false meaning Environmentally Conscious Buyers: Customers interested in sustainability solutions, looking for products that focus on energy management, water conservation, waste reduction, and air quality improvement, or NOT Environmentally Conscious Buyers,
#         The Inventory Manager true or false meaning a purchaser in large amounts to supply an organizational group, versus an individual user purchasing for personal use,
#         The output must be in JSON format inside the tags <attributes></attributes>
#
#         If the information of an entity is not available in the input then don't include that entity in the JSON output
#
#         Begin!
#
#         Customer input: {customer_input}
#         Assistant:""".format(customer_input=customer_input)
#
#         # Process the customer input with the NER model
#         entity_extraction_result = llm(ner_prompt).strip()
#
#         # Extract the attributes from the processed result
#         result = re.search('<attributes>(.*?)</attributes>', entity_extraction_result, re.DOTALL)
#         if result:
#             attributes_str = result.group(1)
#             # Convert the attributes string to JSON
#             attributes = json.loads(attributes_str)
#             end_time = time.time()
#             print("Time for extract_customer_attributes:", end_time - start_time)
#             return attributes
#         else:
#             end_time = time.time()
#             print("Time for extract_customer_attributes:", end_time - start_time)
#             return {}
#
#     @staticmethod
#     def split_process_and_message_from_response(recs_response):
#         start_time = time.time()
#         recs_response = recs_response.strip()  # Remove leading/trailing whitespace
#
#         # Extract the message
#         message_match = re.search('<response>(.*?)</response>', recs_response, re.DOTALL)
#         message = message_match.group(1).strip() if message_match else None
#
#         # Extract the products
#         if "<products>" in recs_response and "</products>" in recs_response:
#             json_content = recs_response[recs_response.index("<products>") + len("<products>"): recs_response.index(
#                 "</products>")].strip()
#
#             try:
#                 parsed_response = json.loads(json_content)
#
#                 if isinstance(parsed_response, list):
#                     products_list = []
#                     for product_info in parsed_response:
#                         product_data = {
#                             "product": product_info.get("product", ""),
#                             "code": product_info.get("code", "")
#                         }
#                         products_list.append(product_data)
#
#                     response_json = {"products": products_list}
#                     end_time = time.time()
#                     print("Time for split_process_and_message_from_response:", end_time - start_time)
#                     return message, response_json
#                 else:
#                     print("Error: Unexpected format of parsed response")
#                     end_time = time.time()
#                     print("Time for split_process_and_message_from_response:", end_time - start_time)
#                     return None, None
#
#             except json.JSONDecodeError as e:
#                 print(f"Error decoding JSON: {str(e)}")
#                 end_time = time.time()
#                 print("Time for split_process_and_message_from_response:", end_time - start_time)
#                 return None, None
#         else:
#             print("Error: Unexpected format of recs_response")
#             end_time = time.time()
#             print("Time for split_process_and_message_from_response:", end_time - start_time)
#             return None, None
#
    def process_chat_question(self, question, clear_history=False):
        start_time = time.time()
        prompt_template3 = """Human: Extract list of upto 5 products and their respective physical IDs from catalog that answer the user question.
            The catalog of products is provided under <catalog></catalog> tags below.
            <catalog>
            {context}
            </catalog>
            Question: {question}

            The output should be a json of the form <products>[{{"product": <description of the product from the catalog>, "code":<code of the product from the catalog>}}, ...]</products> for me to process.
            Also, provide a user-readable message responding in full to the question with all the of the information to display to the user in the form <response>{{message}}</response>.
            Skip the preamble and always return valid json.
            Assistant: """

        PROMPT = PromptTemplate(
            template=prompt_template3, input_variables=["context", "question"]
        )
#
#         # Use RetrievalQA customizations for improving Q&A experience
#         search_index_get_answer_from_llm = RetrievalQA.from_chain_type(
#             llm=self.llm,
#             chain_type="stuff",
#             retriever=self.document.as_retriever(
#                 search_type="similarity", search_kwargs={"k": 6}
#             ),
#             return_source_documents=False,
#             chain_type_kwargs={"prompt": PROMPT},
#         )
#         try:
#             if clear_history:
#                 self.chat_history.clear()  # Clear chat history if specified
#
#             self.chat_history.append([question])
#
#             # Extract product attributes from the question
#             customer_attributes_retrieved = self.extract_customer_attributes(question)
#
#             # Format the customer input with the extracted attributes
#             customer_input_with_attributes = "{} {}".format(question, str(customer_attributes_retrieved))
#
#             # # Retrieve data based on the formatted customer input
#             # retrieved_data_from_index = search_index_get_answer_from_llm({"query": customer_input_with_attributes})['result'] < -- the exact same thing as search_index_get_answer_from_llm.run(**context)
#             #
#             # # Append the retrieved data to the chat history
#             # chat_history.append(retrieved_data_from_index)
#
#             # Prepare the context with the formatted customer input and chat history
#             context = {
#                 'query': customer_input_with_attributes,
#                 'chat_history': self.chat_history
#             }
#
#             # OBTAIN RESPONSE
#             # Run conversation with provided context synchronously
#             llm_retrieval_augmented_response = search_index_get_answer_from_llm.run(**context)
#             # print(llm_retrieval_augmented_response)
#             message, product_list_as_json = self.split_process_and_message_from_response(llm_retrieval_augmented_response)
#
#             # UPDATE HISTORY
#             if product_list_as_json is not None:
#                 self.chat_history.append(product_list_as_json['products'])
#
#             # if reviews_dict is not None:
#             #     chat_history.append(reviews_dict)
#
#             end_time = time.time()
#             total_time = end_time - start_time
#             print("Time for process_chat_question:", total_time)
#             return message, product_list_as_json, total_time
#
#         except ValueError as error:
#             if "AccessDeniedException" in str(error):
#                 class StopExecution(ValueError):
#                     def _render_traceback_(self):
#                         pass
#
#                 end_time = time.time()
#                 print("Time for process_chat_question:", end_time - start_time)
#                 raise StopExecution
#             else:
#                 end_time = time.time()
#                 print("Time for process_chat_question:", end_time - start_time)
#                 raise error
#
#
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
