import time
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

from .customer_attributes import extract_customer_attributes
from .response_parser import split_process_and_message_from_response


def process_chat_question_with_customer_attribute_identifier(question, document, llm, chat_history, clear_history=False):
    start_time = time.time()
    prompt_template3 = """Human: Extract list of products (do not repeat or duplicate) and their respective physical IDs 
                        from catalog that answer the user question.
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
        if clear_history:
            chat_history.clear()

        chat_history.append([question])

        customer_attributes_retrieved = extract_customer_attributes(question, llm)

        customer_input_with_attributes = "{} {}".format(question, str(customer_attributes_retrieved))

        context = {
            'query': customer_input_with_attributes,
            'chat_history': chat_history
        }

        llm_retrieval_augmented_response = search_index_get_answer_from_llm.run(**context)
        message, product_list_as_json = split_process_and_message_from_response(llm_retrieval_augmented_response)

        if product_list_as_json is not None:
            chat_history.append(product_list_as_json['products'])

        end_time = time.time()
        total_time = end_time - start_time
        print("Time for process_chat_question:", total_time)
        return message, product_list_as_json, total_time

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
