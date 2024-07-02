import time

import streamlit as st

from vector_index import Document as vectorIndexDocument
from vector_index.chat_processor import process_chat_question


class StreamlitInterface:
    def __init__(self, index_document, LLM, bedrock_titan_embeddings):
        self.document = index_document
        self.llm = LLM
        self.bedrock_embeddings = bedrock_titan_embeddings
        self.chat_history = []

    def ask_question(self):
        question = st.text_input("Enter your question:", value="", placeholder="")
        start_time = time.time()
        if question:
            response, products, time_taken = self.process_chat_question(question=question, clear_history=False)
            st.write("Response:", response)
            st.write("Time taken:", time_taken)
        end_time = time.time()
        st.write("Total time for ask_question:", end_time - start_time)

    def process_chat_question(self, question, clear_history=False):
        return process_chat_question(question, self.document, self.llm, self.chat_history, clear_history)

    def run(self):
        start_time = time.time()
        st.title("Ask a Question")
        self.ask_question()
        end_time = time.time()
        st.write("Total time for run:", end_time - start_time)


if __name__ == "__main__":
    document, llm, bedrock_embeddings = vectorIndexDocument.get_instance()
    interface = StreamlitInterface(index_document=document, LLM=llm, bedrock_titan_embeddings=bedrock_embeddings)
    interface.run()
