import os
import pickle

from langchain_aws import Bedrock
from langchain.embeddings import BedrockEmbeddings
from langchain.vectorstores import FAISS
from .bedrock_initializer import bedrock
import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
class Document:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata

def initialize_embeddings_and_faiss():
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    # os.environ["AWS_PROFILE"] = ""
    # os.environ["BEDROCK_ASSUME_ROLE"] = ""  # E.g. "arn:aws:..."

    boto3_bedrock = bedrock.get_bedrock_client(
        assumed_role=os.environ.get("BEDROCK_ASSUME_ROLE", None),
        region=os.environ.get("AWS_DEFAULT_REGION", None),
        runtime=False)

    bedrock_runtime = bedrock.get_bedrock_client(
        assumed_role=os.environ.get("BEDROCK_ASSUME_ROLE", None),
        region=os.environ.get("AWS_DEFAULT_REGION", None))

    model_parameter = {
        "temperature": 0.0,
        "top_p": .5,
        "top_k": 250,
        "max_tokens_to_sample": 2000,
        "stop_sequences": ["\n\n Human: bye"]
    }
    llm = Bedrock(
        model_id="anthropic.claude-v2",
        model_kwargs=model_parameter,
        client=bedrock_runtime
    )
    # Initialize the Titan Embeddings Model
    print("Initializing Titan Embeddings Model...")
    bedrock_embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1", client=bedrock_runtime)
    print("Titan Embeddings Model initialized.")

    # Load the processed data
    parquet_file_directory = "vector_index/processed"
    parquet_file_path = os.path.join(parquet_file_directory, "grainger_products.parquet")

    # "modules/vector_index/processed/grainger_products.parquet"
    print("Attempting to load file from:", parquet_file_path)
    # Now attempt to load the file
    try:
        df = pd.read_parquet("modules/vector_index/processed/grainger_products.parquet")
        print(df.head())
        print("File loaded successfully!")
    except FileNotFoundError as e:
        print("Error loading file:", e)

    documents = []
    for index, row in df.iterrows():
        #TODO REMOVE SIZE CONSTRAINT
        if index < 400:
            page_content = f"{row['Code']} {row['Name']} {row['Brand']} {row['Description'] if pd.notna(row['Description']) else ''}"
            metadata = {
                'Brand': row['Brand'],
                'Code': row['Code'],
                'Name': row['Name'],
                'Description': row['Description'],
                'Price': row['Price']
            }
            documents.append(Document(page_content, metadata))

    print("Structured documents created:")
    for idx, doc in enumerate(documents[:5], 1):
        print(f"Document {idx} of {len(documents)}:")
        print(doc.page_content[:200])
        print()

    # Create FAISS vector store from structured documents
    print("Creating FAISS vector store from structured documents...")
    vectorstore_faiss_doc = FAISS.from_documents(documents, bedrock_embeddings)


    print("FAISS vector store created.")

    #  SERIALIZE
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, 'shopping_queries_dataset')
    products_file = os.path.join(output_dir, 'processed_products.parquet')
    serialized_file = os.path.join(base_dir, 'vector_index.pkl')
    # Check if the serialized file already exists
    if os.path.exists(serialized_file):
        logging.info(f"Serialized file {serialized_file} already exists. Deleting it.")
        os.remove(serialized_file)
        logging.info(f"Deleted old version of {serialized_file}")

    logging.info(f"Initializing VectorIndex instance from {products_file}")
    vector_index_instance = vectorstore_faiss_doc.serialize_to_bytes()
    if vector_index_instance is None:
        raise ValueError("Failed to initialize VectorIndex instance")

    logging.info("VectorIndex instance initialized")

    # Serialize the VectorIndex instance to a file
    logging.info("Starting Pickle Dump")
    with open(serialized_file, 'wb') as file:
        pickle.dump(vector_index_instance, file)
        logging.info("Completed Pickle Dump")



    return bedrock_embeddings, vectorstore_faiss_doc, df, llm

def get_instance(cls, **kwargs):
        """Static access method to get the singleton instance, enforcing required arguments."""
        logging.info("Entering get_instance method")
        if cls._instance is None:
            logging.info("Instance is None, creating new instance")
            pickle_file = kwargs.get('pickle_file', 'vector_index.pkl')
            products_file = kwargs.get('products_file', '')

            # Check if 'products_file' is a string
            if not isinstance(products_file, str):
                logging.error("'products_file' argument must be a string")
                raise TypeError("'products_file' argument must be a string")

            if os.path.exists(pickle_file):
                logging.info(f"Loading VectorIndex instance from {pickle_file}")
                try:
                    with open(pickle_file, 'rb') as file:
                        cls._instance = pickle.load(file)
                    logging.info("VectorIndex instance loaded from pickle file.")
                except Exception as e:
                    logging.error(f"Failed to load VectorIndex from pickle file: {e}")
                    raise
            else:
                logging.info("Creating new instance of VectorIndex...")
                cls._instance = cls(products_file=products_file)
                try:
                    cls._instance.verify_or_wait_for_file_creation()
                    cls._instance.load_processed_products()
                    cls._instance.create_faiss_index()
                    with open(pickle_file, 'wb') as file:
                        pickle.dump(cls._instance, file)
                    logging.info("VectorIndex instance created and serialized to pickle file.")
                except Exception as e:
                    logging.error(f"Failed to initialize the FAISS index: {str(e)}")
                    raise RuntimeError(f"Error initializing the FAISS index: {str(e)}")
        else:
            logging.info("Using existing instance of VectorIndex")

        return cls._instance

# import os
# import pandas as pd
# from langchain.embeddings import BedrockEmbeddings
# from langchain.vectorstores import FAISS
# from .bedrock_initializer import LLMInitializer
#
# class Document:
#     def __init__(self, page_content, metadata):
#         self.page_content = page_content
#         self.metadata = metadata
#
# def initialize_faiss_vector_store(df, bedrock_runtime):
#     # Initialize the Titan Embeddings Model
#     print("Initializing Titan Embeddings Model...")
#     bedrock_embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1", client=bedrock_runtime)
#     print("Titan Embeddings Model initialized.")
#
#     documents = []
#     for _, row in df.iterrows():
#         page_content = f"{row['Code']} {row['Name']} {row['Brand']} {row['Description'] if pd.notna(row['Description']) else ''}"
#         metadata = {
#             'Brand': row['Brand'],
#             'Code': row['Code'],
#             'Name': row['Name'],
#             'Description': row['Description'],
#             'Price': row['Price']
#         }
#         documents.append(Document(page_content, metadata))
#
#     print("Structured documents created:")
#     for idx, doc in enumerate(documents[:5], 1):
#         print(f"Document {idx} of {len(documents)}:")
#         print(doc.page_content[:200])
#         print()
#
#     # Create FAISS vector store from structured documents
#     print("Creating FAISS vector store from structured documents...")
#     vectorstore_faiss_doc = FAISS.from_documents(documents, bedrock_embeddings)
#     print("FAISS vector store created.")
#
#     return bedrock_embeddings, vectorstore_faiss_doc
#
# def main():
#     parquet_file_directory = "vector_index/processed"
#     parquet_file_path = os.path.join(parquet_file_directory, "grainger_products.parquet")
#
#     # "modules/vector_index/processed/grainger_products.parquet"
#
#     print("Attempting to load file from:", parquet_file_path)
#
#     # Now attempt to load the file
#     try:
#         df = pd.read_parquet("modules/vector_index/processed/grainger_products.parquet")
#         print(df.head())
#         print("File loaded successfully!")
#     except FileNotFoundError as e:
#         print("Error loading file:", e)
#
#     llm_initializer = LLMInitializer()
#     llm, bedrock_runtime = llm_initializer.check_and_initialize_llm()
#     initialize_faiss_vector_store(df, bedrock_runtime)
#
# if __name__ == "__main__":
#     main()
#
#
#
#
#
#
#
#
#
#
#
#
# # import os
# # import time
# # import threading
# # from datetime import datetime
# #
# # import pandas as pd
# # import numpy as np
# # import transformers
# # from langchain_community.embeddings import BedrockEmbeddings
# # from langchain_community.vectorstores import FAISS
# #
# # from bedrock_initializer import bedrock_runtime
# # import logging
# #
# # from data_frame_initializer import DataFrameSingleton
# #
# # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# #
# #
# # def print_processing():
# #     print("Processing...")
# #     threading.Timer(30.0, print_processing).start()
# #
# #
# # def log_creation_time(file_path):
# #     ctime = os.path.getctime(file_path)
# #     creation_time = datetime.fromtimestamp(ctime).strftime('%Y-%m-%d %H:%M:%S')
# #     print(f"File '{file_path}' was created on {creation_time}")
# #
# #
# # class Document:
# #     _vector_index = None  # Class variable to store the vector index
# #
# #     def __init__(self, page_content, metadata):
# #         self.page_content = page_content
# #         self.metadata = metadata
# #
# #     @classmethod
# #     def get_instance(cls, **kwargs):
# #         """Static access method to get the singleton instance, enforcing required arguments."""
# #         logging.info("Entering get_instance method")
# #
# #         if cls._vector_index is None:
# #             # Initialize the Titan Embeddings Model only if the vector index has not been created yet
# #             print("Initializing Titan Embeddings Model...")
# #             bedrock_embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1", client=bedrock_runtime)
# #             print("Titan Embeddings Model initialized.")
# #
# #             documents = []
# #             data_frame_singleton = DataFrameSingleton.get_instance()
# #             df = data_frame_singleton.df
# #             for _, row in df.iterrows():
# #                 page_content = f"{row['Code']} {row['Name']} {row['Brand']} {row['Description'] if pd.notna(row['Description']) else ''}"
# #                 metadata = {
# #                     'Brand': row['Brand'],
# #                     'Code': row['Code'],
# #                     'Name': row['Name'],
# #                     'Description': row['Description'],
# #                     'Price': row['Price']
# #                 }
# #                 documents.append(Document(page_content, metadata))
# #
# #             # Print the structured documents
# #             print("Structured documents created:")
# #             for idx, doc in enumerate(documents[:5], 1):
# #                 print(f"Document {idx} of {len(documents)}:")
# #                 print(doc.page_content[:200])
# #                 print()
# #
# #             # Create FAISS vector store from structured documents
# #             print("Creating FAISS vector store from structured documents...")
# #             start_time = time.time()
# #             print_processing()
# #             cls._vector_index = FAISS.from_documents(documents, bedrock_embeddings)
# #             end_time = time.time()
# #             time_taken = end_time - start_time
# #             print(f"Created FAISS vector store from structured documents in {time_taken} seconds.")
# #
# #         return cls._vector_index
# #
# #
# #
# #
# #
# # # import time
# # # import os
# # # import pandas as pd
# # # import logging
# # # from datetime import datetime
# # # from langchain.embeddings import BedrockEmbeddings
# # # from langchain.vectorstores import FAISS
# # # from langchain.indexes.vectorstore import VectorStoreIndexWrapper
# # # from langchain.text_splitter import RecursiveCharacterTextSplitter
# # # from langchain.document_loaders import DirectoryLoader
# # # from langchain.document_loaders import S3FileLoader
# # # from bedrock_initializer import LLMInitializer
# # # from data_frame_initializer import DataFrameSingleton
# # # # from .bedrock_initializer import LLMInitializer
# # # # from .data_frame_initializer import DataFrameSingleton
# # #
# # #
# # #
# # # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# # #
# # #
# # # def log_creation_time(file_path):
# # #     ctime = os.path.getctime(file_path)
# # #     creation_time = datetime.fromtimestamp(ctime).strftime('%Y-%m-%d %H:%M:%S')
# # #     logging.info(f"File '{file_path}' was created on {creation_time}")
# # #
# # #
# # # class Document:
# # #     _instance = None
# # #     _vector_index = None
# # #     _df = None
# # #     _llm = None
# # #     _bedrock_embeddings = None
# # #
# # #     def __new__(cls, *args, **kwargs):
# # #         if cls._instance is None:
# # #             cls._instance = super(Document, cls).__new__(cls)
# # #         return cls._instance
# # #
# # #     def __init__(self, page_content, metadata):
# # #         self.page_content = page_content
# # #         self.metadata = metadata
# # #
# # #     @classmethod
# # #     def get_instance(cls, **kwargs):
# # #         """Static access method to get the singleton instance, enforcing required arguments."""
# # #         logging.info("Entering get_instance method")
# # #
# # #         if cls._vector_index is None or cls._df is None:
# # #             cls._llm = cls.initialize_llm()
# # #             cls._bedrock_embeddings = cls.initialize_bedrock()
# # #             documents = []
# # #             data_frame_singleton = DataFrameSingleton.get_instance()
# # #             cls._df = data_frame_singleton.df
# # #
# # #             logging.info(f"DataFrame contains {cls._df.shape[0]} rows")
# # #
# # #             for idx, (_, row) in enumerate(cls._df.iterrows()):
# # #                 logging.info(f"Processing row {idx + 1}/{cls._df.shape[0]} with code: {row['Code']}")
# # #                 page_content = f"{row['Code']} {row['Name']} {row['Brand']} {row['Description'] if pd.notna(row['Description']) else ''}"
# # #                 metadata = {
# # #                     'Brand': row['Brand'],
# # #                     'Code': row['Code'],
# # #                     'Name': row['Name'],
# # #                     'Description': row['Description'],
# # #                     'Price': row['Price']
# # #                 }
# # #
# # #                 logging.debug(f"Page content for document {idx + 1}: {page_content}")
# # #                 logging.debug(f"Metadata for document {idx + 1}: {metadata}")
# # #
# # #                 # Check if the document is unique before appending
# # #                 if not any(doc.page_content == page_content for doc in documents):
# # #                     documents.append(Document(page_content, metadata))
# # #                 else:
# # #                     logging.warning(f"Duplicate document found for code: {row['Code']}")
# # #
# # #             # Print the structured documents
# # #             logging.info("Structured documents created:")
# # #             for idx, doc in enumerate(documents[:5], 1):
# # #                 logging.info(f"Document {idx} of {len(documents)}:")
# # #                 logging.info(doc.page_content[:200])
# # #
# # #             # Create FAISS vector store from structured documents
# # #             logging.info("Creating FAISS vector store from structured documents...:", documents.pop().page_content[:200])
# # #             start_time = time.time()
# # #             cls._vector_index = FAISS.from_documents(documents=documents, embedding=cls._bedrock_embeddings)
# # #             end_time = time.time()
# # #             time_taken = end_time - start_time
# # #             logging.info(f"Created FAISS vector store from structured documents in {time_taken} seconds.")
# # #
# # #         return cls._vector_index, cls._llm, cls._bedrock_embeddings, cls._df
# # #
# # #     @classmethod
# # #     def recreate_index(cls, **kwargs):
# # #         """Method to force the recreation of the vector index."""
# # #         logging.info("Entering recreate_index method")
# # #         cls._vector_index = None
# # #         return cls.get_instance(**kwargs)
# # #
# # #     @classmethod
# # #     def initialize_llm(cls):
# # #         logging.info("Setting up LLM")
# # #         llm_initializer = LLMInitializer()
# # #         llm, bedrock_runtime = llm_initializer.check_and_initialize_llm()
# # #         if llm is None:
# # #             logging.warning("Failed to initialize LLM")
# # #             raise ValueError("Failed to initialize LLM")
# # #         cls._llm = llm
# # #         cls._bedrock_runtime = bedrock_runtime
# # #         logging.info("LLM initialized")
# # #         return cls._llm
# # #
# # #     @classmethod
# # #     def initialize_bedrock(cls):
# # #         logging.info("Initializing Titan Embeddings Model...")
# # #         bedrock_embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1", client=cls._bedrock_runtime)
# # #         logging.info("Titan Embeddings Model initialized.")
# # #         return bedrock_embeddings
