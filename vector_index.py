import os
import time
import threading
from datetime import datetime

import pandas as pd
import numpy as np
import transformers
from langchain_community.embeddings import BedrockEmbeddings
from langchain_community.vectorstores import FAISS

from bedrock_initializer import bedrock_runtime
import logging

from data_frame_initializer import DataFrameSingleton

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def print_processing():
    print("Processing...")
    threading.Timer(30.0, print_processing).start()


def log_creation_time(file_path):
    ctime = os.path.getctime(file_path)
    creation_time = datetime.fromtimestamp(ctime).strftime('%Y-%m-%d %H:%M:%S')
    print(f"File '{file_path}' was created on {creation_time}")


class Document:
    _vector_index = None  # Class variable to store the vector index

    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata

    @classmethod
    def get_instance(cls, **kwargs):
        """Static access method to get the singleton instance, enforcing required arguments."""
        logging.info("Entering get_instance method")

        if cls._vector_index is None:
            # Initialize the Titan Embeddings Model only if the vector index has not been created yet
            print("Initializing Titan Embeddings Model...")
            bedrock_embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1", client=bedrock_runtime)
            print("Titan Embeddings Model initialized.")

            documents = []
            data_frame_singleton = DataFrameSingleton.get_instance()
            df = data_frame_singleton.df
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
            print("Structured documents created:")
            for idx, doc in enumerate(documents[:5], 1):
                print(f"Document {idx} of {len(documents)}:")
                print(doc.page_content[:200])
                print()

            # Create FAISS vector store from structured documents
            print("Creating FAISS vector store from structured documents...")
            start_time = time.time()
            print_processing()
            cls._vector_index = FAISS.from_documents(documents, bedrock_embeddings)
            end_time = time.time()
            time_taken = end_time - start_time
            print(f"Created FAISS vector store from structured documents in {time_taken} seconds.")

        return cls._vector_index
