import time
import os
import pandas as pd
import logging
from datetime import datetime
from langchain_community.embeddings import BedrockEmbeddings
from langchain.vectorstores import FAISS
from data_frame_initializer import DataFrameSingleton
from bedrock_initializer import LLMInitializer


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def log_creation_time(file_path):
    ctime = os.path.getctime(file_path)
    creation_time = datetime.fromtimestamp(ctime).strftime('%Y-%m-%d %H:%M:%S')
    logging.info(f"File '{file_path}' was created on {creation_time}")


class Document:
    _instance = None
    _vector_index = None
    _llm = None
    _bedrock_embeddings = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Document, cls).__new__(cls)
        return cls._instance

    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata

    @classmethod
    def get_instance(cls, **kwargs):
        """Static access method to get the singleton instance, enforcing required arguments."""
        logging.info("Entering get_instance method")

        if cls._vector_index is None:
            cls._llm = cls.initialize_llm()
            cls._bedrock_embeddings = cls.initialize_bedrock()
            documents = []
            data_frame_singleton = DataFrameSingleton.get_instance()
            #TODO: Change the fraction to 1.0 when not testing
            df = data_frame_singleton.df #.sample(frac=0.1)
            for _, row in df.iterrows():
                page_content = f"{row['Code']} {row['Name']} {row['Brand']} {row['Description'] if pd.notna(row['Description']) else ''}"
                metadata = {
                    'Brand': row['Brand'],
                    'Code': row['Code'],
                    'Name': row['Name'],
                    'Description': row['Description'],
                    'Price': row['Price']
                }
                documents.append(Document(page_content, metadata))

            # Print the structured documents
            logging.info("Structured documents created:")
            for idx, doc in enumerate(documents[:2], 1):
                logging.info(f"Document {idx} of {len(documents)}:")
                logging.info(doc.page_content[:200])

            # Create FAISS vector store from structured documents
            logging.info("Creating FAISS vector store from structured documents...")
            start_time = time.time()
            cls._vector_index = FAISS.from_documents(documents=documents, embedding=cls._bedrock_embeddings)
            end_time = time.time()
            time_taken = end_time - start_time
            logging.info(f"Created FAISS vector store from structured documents in {time_taken} seconds.")

        return cls._vector_index, cls._llm, cls._bedrock_embeddings

    @classmethod
    def recreate_index(cls, **kwargs):
        """Method to force the recreation of the vector index."""
        logging.info("Entering recreate_index method")
        cls._vector_index = None
        return cls.get_instance(**kwargs)

    @classmethod
    def initialize_llm(cls):
        logging.info("Setting up LLM")
        llm_initializer = LLMInitializer()
        llm, bedrock_runtime = llm_initializer.check_and_initialize_llm()
        if llm is None:
            logging.warn("Failed to initialize LLM")
            raise ValueError("Failed to initialize LLM")
        cls._llm = llm
        cls._bedrock_runtime = bedrock_runtime
        logging.info("LLM initialized")
        return cls._llm

    @classmethod
    def initialize_bedrock(cls):
        logging.info("Initializing Titan Embeddings Model...")
        bedrock_embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1", client=cls._bedrock_runtime)
        logging.info("Titan Embeddings Model initialized.")
        return bedrock_embeddings
