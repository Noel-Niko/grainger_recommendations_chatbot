import streamlit as st

from vector_index import Document
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

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
    def __init__(self, document, llm):
        self.document = document
        self.llm = llm

    def ask_question(self):
        question = st.text_input("Enter your question:", value="", placeholder="")
        if question:
            qa = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.document.as_retriever(
                    search_type="similarity", search_kwargs={"k": 6}
                ),
                return_source_documents=False,
                chain_type_kwargs={"prompt": PROMPT},
            )

            response = qa
            st.write("Response:", response)

    def run(self):
        st.title("Ask a Question")
        self.ask_question()


if __name__ == "__main__":
    document, llm = Document.get_instance()
    interface = StreamlitInterface(document, llm)
    interface.run()

#
# class StreamlitInterface:
#     def __init__(self):
#         self.document = None
#
#     def ask_question(self):
#         question = st.text_input("Enter your question:", value="", placeholder="")
#         if question:
#             # Use RetrievalQA customizations for improving Q&A experience
#             qa = RetrievalQA.from_chain_type(
#                 llm=llm,
#                 chain_type="stuff",
#                 retriever=self.document.as_retriever(
#                     search_type="similarity", search_kwargs={"k": 6}
#                 ),
#                 return_source_documents=False,
#                 chain_type_kwargs={"prompt": PROMPT},
#             )
#
#             response = qa
#             st.write("Response:", response)
#
#     def run(self):
#         st.title("Ask a Question")
#         self.document = Document.get_instance()
#         self.ask_question()
#
#
# if __name__ == "__main__":
#     interface = StreamlitInterface()
#     interface.run()
