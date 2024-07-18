import logging
import sys
import time
import json

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

from .customer_attributes import extract_customer_attributes
from .response_parser import split_process_and_message_from_response

tag = 'chat_processor'

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

def process_chat_question_with_customer_attribute_identifier(question, document, llm, chat_history):
    start_time = time.time()
    prompt_template = """Human: Extract a list of products (do not repeat or duplicate) and their respective Codes 
                        from catalog that answer the user question.
                The catalog of products is provided under <catalog></catalog> tags below.
                <catalog>
                {context}
                </catalog>
                Question: {question}

                The output should be a json of the form <products>[{{"product": <description of the product from the catalog>, "code":<code of the product from the catalog>}}, ...]</products> for me to process.
                Also, provide a user-readable message responding in full to the question speaking as a friendly salesperson chatbot with all the of the information to display to the user in the form <response>{{message}}</response>.
                Skip the preamble and always return valid json including empty json if not products are found.
                Assistant: """

    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    search_index_get_answer_from_llm = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=document.as_retriever(
            search_type="similarity", search_kwargs={"k": 6}
        ),
        return_source_documents=False,
        chain_type_kwargs={"prompt": PROMPT},
    )
    try:
        customer_attributes_retrieved = extract_customer_attributes(question, llm)
        time_to_get_attributes = time.time() - start_time
        customer_input_with_attributes = "{} {}".format(question, str(customer_attributes_retrieved))
        # logging.info(f"{tag}/ Chat History passed to processor: {chat_history}")
        context = {
            'query': customer_input_with_attributes,
            'chat_history': chat_history.copy()
        }

        llm_retrieval_augmented_response = search_index_get_answer_from_llm.run(**context)
        message, product_list_as_json = split_process_and_message_from_response(llm_retrieval_augmented_response)
        # logging.info(f"{tag}/ chat_procesing: message: {message}")
        # logging.info(f"{tag}/ chat_procesing: product_list_as_json: {product_list_as_json}")

        # Ensure product_list_as_json is valid JSON
        logging.info(f"{tag}/ product_list_as_json: {product_list_as_json}")
        try:
            # Convert to string if not already
            if isinstance(product_list_as_json, dict):
                product_list_as_json = json.dumps(product_list_as_json)
            # Attempt to load JSON directly
            product_list_as_json = json.loads(product_list_as_json)
            logging.info(f"{tag}/ product_list_as_json processed")
        except json.JSONDecodeError:
            logging.warning(f"{tag}/ Invalid JSON format detected. Attempting to fix.")
            try:
                # Attempt to fix JSON format by replacing single quotes with double quotes
                fixed_json_str = product_list_as_json.replace("'", '"')
                product_list_as_json = json.loads(fixed_json_str)
                logging.info(f"{tag}/ Fixed JSON: {product_list_as_json}")
            except json.JSONDecodeError as e:
                logging.error(f"{tag}/ Failed to fix JSON format: {str(e)}")
                product_list_as_json = None

        return message, product_list_as_json, str(customer_attributes_retrieved), time_to_get_attributes

    except ValueError as error:
        if "AccessDeniedException" in str(error):
            class StopExecution(ValueError):
                def _render_traceback_(self):
                    pass

            end_time = time.time()
            print("Time for process_chat_question:", end_time - start_time)
            raise StopExecution
        else:
            end_time = time.time()
            print("Time for process_chat_question:", end_time - start_time)
            raise error
