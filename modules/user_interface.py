import numpy as np
import streamlit as st

from vector_index import Document as vectorIndexDocument
# from langchain.chains import RetrievalQA
# from langchain.prompts import PromptTemplate
# from langchain.chains import conversation
from langchain.chains import RetrievalQA
# from langchain.chains import create_history_aware_retriever, create_retrieval_chain
# from langchain.chains.combine_documents import create_stuff_documents_chain
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import PromptTemplate
from langchain.chains.conversational_retrieval.prompts import QA_PROMPT
from langchain.llms.bedrock import Bedrock
from langchain.chains import LLMChain

# class MyPromptTemplate(PromptTemplate):
#     def __init__(self, template, input_variables):
#         self.template = template
#         self.input_variables = input_variables
#
#     def format(self, *args, **kwargs):
#         # Your implementation here
#         pass
#
#     def format_prompt(self, *args, **kwargs):
#         # Your implementation here
#         pass


prompt_template2 = """Human: Extract list of 5 products and their respective physical IDs from catalog that answer the user question. 
The catalog of products is provided under <catalog></catalog> tags below.
<catalog>
{context}
</catalog>
Question: {question}

The output should be a json of the form <products>[{{"product": <description of the product from the catalog>, "code":<code of the product from the catalog>}}, ...]</products>
Skip the preamble and always return valid json.
Assistant: """
PROMPT = PromptTemplate(
    template=prompt_template2, input_variables=["context", "question"]
)


class StreamlitInterface:
    def __init__(self, index_document, LLM, bedrock_titan_embeddings):
        self.document = index_document
        self.llm = LLM
        self.bedrock_embeddings = bedrock_titan_embeddings
        self.chat_history = []

    def ask_question(self):
        question = st.text_input("Enter your question:", value="", placeholder="")

        if question:
            # query_embedding_doc = bedrock_embeddings.embed_query(question)
            # np_array_query_embedding_doc = np.array(query_embedding_doc)
            # print("Customer input processed.")
            llm_chain = LLMChain(
                llm=self.llm,
                input_variables=["chat_history", "question", "document"],  # Include 'document'
            )

            qa = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.document.as_retriever(
                    search_type="similarity", search_kwargs={"k": 6}
                ),
                return_source_documents=False,
                chain_type_kwargs={"prompt": QA_PROMPT},
                document_variable_name="context",
            )

            response = self.process_chat_question(question=question, qa=qa, clear_history=False)

            st.write("Response:", response)

    def process_chat_question(self, question, qa, clear_history=False):
        try:
            if clear_history:
                self.chat_history.clear()  # Clear chat history if specified

            # Extract product attributes from the question
            # customer_attributes = extract_product_attributes(question)

            # Format the customer input with the extracted attributes
            # customer_input = "{} {}".format(question, str(customer_attributes))

            # Retrieve data based on the formatted customer input
            retrieved_data = qa({"query": question})['result']

            # Append the retrieved data to the chat history
            self.chat_history.append(retrieved_data)

            # Prepare the context with the formatted customer input and chat history
            context = {
                'question': question,
                'chat_history': self.chat_history
            }

            # # # Run conversation with provided context synchronously
            # chat_res = conversation.run(**context)
            #
            # # Append the chat prompt and result to history
            # self.chat_history.append([question, chat_res])

            # Optionally add response_json['products'] and reviews_dict to chat history
            # if response_json is not None:
            #     chat_history.append(response_json['products'])

            # if reviews_dict is not None:
            #     chat_history.append(reviews_dict)

            return str(retrieved_data)  # Return chat response as a string

        except ValueError as error:
            if "AccessDeniedException" in str(error):
                class StopExecution(ValueError):
                    def _render_traceback_(self):
                        pass

                raise StopExecution
            else:
                raise error

    def run(self):
        st.title("Ask a Question")
        self.ask_question()


if __name__ == "__main__":
    document, llm, bedrock_embeddings = vectorIndexDocument.get_instance()
    interface = StreamlitInterface(index_document=document, LLM=llm, bedrock_titan_embeddings=bedrock_embeddings)
    interface.run()
