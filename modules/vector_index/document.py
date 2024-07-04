import os
import pickle
import pandas as pd
import logging
from langchain_aws import Bedrock
from langchain.embeddings import BedrockEmbeddings
from langchain.vectorstores import FAISS
from langchain_core.vectorstores import VectorStoreRetriever

from .bedrock_initializer import bedrock

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Document:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata


def initialize_embeddings_and_faiss():
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

    # Initialize Bedrock clients
    boto3_bedrock = bedrock.get_bedrock_client(
        assumed_role=os.environ.get("BEDROCK_ASSUME_ROLE", None),
        region=os.environ.get("AWS_DEFAULT_REGION", None),
        runtime=False
    )
    bedrock_runtime = bedrock.get_bedrock_client(
        assumed_role=os.environ.get("BEDROCK_ASSUME_ROLE", None),
        region=os.environ.get("AWS_DEFAULT_REGION", None)
    )

    # Load or create LLM instance
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

    # Initialize Titan Embeddings Model
    logging.info("Initializing Titan Embeddings Model...")
    bedrock_embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1", client=bedrock_runtime)
    logging.info("Titan Embeddings Model initialized.")

    # Load processed data from Parquet file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parquet_file_path = os.path.join(os.path.join(current_dir, "processed/grainger_products.parquet"))
    logging.info("Attempting to load file from:", parquet_file_path)
    # Load processed data from Parquet file
    documents = []
    df = pd.read_parquet(parquet_file_path)



    serialized_documents_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'documents.pkl')
    if os.path.exists(serialized_documents_file):
        logging.info(f"Serialized documents file {serialized_documents_file} already exists. Loading...")
        with open(serialized_documents_file, 'rb') as file:
            documents = pickle.load(open(serialized_documents_file, "rb"))
            logging.info("Documents file loaded successfully!")
    else:
        logging.error("Error loading serialized_documents_file")
        logging.info("Generating new df")
        for index, row in df.iterrows():
            page_content = f"{row['Code']} {row['Name']} {row['Brand']} {row['Description'] if pd.notna(row['Description']) else ''}"
            metadata = {
                'Brand': row['Brand'],
                'Code': row['Code'],
                'Name': row['Name'],
                'Description': row['Description'],
                'Price': row['Price']
            }
            documents.append(Document(page_content, metadata))
            logging.info("Structured documents created:")
            for idx, doc in enumerate(documents[:5], 1):
                logging.info(f"Document {idx} of {len(documents)}:")
                logging.info(doc.page_content[:200])
            pickle.dump(documents, open("documents.pkl", "wb"))

    # Check if serialized FAISS index exists
    serialized_index_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vector_index.pkl')
    if os.path.exists(serialized_index_file):
        logging.info(f"Serialized file {serialized_index_file} already exists. Loading...")
        with open(serialized_index_file, 'rb') as file:
            pickle_data = pickle.load(file)
            vectorstore_faiss_doc = FAISS.deserialize_from_bytes(embeddings=bedrock_embeddings, serialized=pickle_data,
                                                                 allow_dangerous_deserialization=True)
        logging.info("FAISS vector store loaded from pickle file.")
    else:
        logging.info("Creating FAISS vector store from structured documents...")
        vectorstore_faiss_doc = FAISS.from_documents(documents, bedrock_embeddings)
        logging.info("FAISS vector store created.")

        # Serialize FAISS vector store to pickle file
        logging.info(f"Serializing FAISS vector store to {serialized_index_file}")
        with open(serialized_index_file, 'wb') as file:
            serialized_vector = vectorstore_faiss_doc.serialize_to_bytes()
            pickle.dump(serialized_vector, file)
        logging.info("FAISS vector store serialized to pickle file.")

    return bedrock_embeddings, vectorstore_faiss_doc, df, llm

# import os
# import pickle
#
# from langchain_aws import Bedrock
# from langchain.embeddings import BedrockEmbeddings
# from langchain.vectorstores import FAISS
# from .bedrock_initializer import bedrock
# import pandas as pd
# import numpy as np
# import logging
#
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# class Document:
#     def __init__(self, page_content, metadata):
#         self.page_content = page_content
#         self.metadata = metadata
#
# def initialize_embeddings_and_faiss():
#     os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
#     # os.environ["AWS_PROFILE"] = ""
#     # os.environ["BEDROCK_ASSUME_ROLE"] = ""  # E.g. "arn:aws:..."
#
#     boto3_bedrock = bedrock.get_bedrock_client(
#         assumed_role=os.environ.get("BEDROCK_ASSUME_ROLE", None),
#         region=os.environ.get("AWS_DEFAULT_REGION", None),
#         runtime=False)
#
#     bedrock_runtime = bedrock.get_bedrock_client(
#         assumed_role=os.environ.get("BEDROCK_ASSUME_ROLE", None),
#         region=os.environ.get("AWS_DEFAULT_REGION", None))
#
#     model_parameter = {
#         "temperature": 0.0,
#         "top_p": .5,
#         "top_k": 250,
#         "max_tokens_to_sample": 2000,
#         "stop_sequences": ["\n\n Human: bye"]
#     }
#     llm = Bedrock(
#         model_id="anthropic.claude-v2",
#         model_kwargs=model_parameter,
#         client=bedrock_runtime
#     )
#     # Initialize the Titan Embeddings Model
#     print("Initializing Titan Embeddings Model...")
#     bedrock_embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1", client=bedrock_runtime)
#     print("Titan Embeddings Model initialized.")
#
#     # Load the processed data
#     parquet_file_directory = "vector_index/processed"
#     parquet_file_path = os.path.join(parquet_file_directory, "grainger_products.parquet")
#
#     # "modules/vector_index/processed/grainger_products.parquet"
#     print("Attempting to load file from:", parquet_file_path)
#     # Now attempt to load the file
#     try:
#         df = pd.read_parquet("modules/vector_index/processed/grainger_products.parquet")
#         print(df.head())
#         print("File loaded successfully!")
#     except FileNotFoundError as e:
#         print("Error loading file:", e)
#
#     documents = []
#     for index, row in df.iterrows():
#         #TODO REMOVE SIZE CONSTRAINT
#         if index < 400:
#             page_content = f"{row['Code']} {row['Name']} {row['Brand']} {row['Description'] if pd.notna(row['Description']) else ''}"
#             metadata = {
#                 'Brand': row['Brand'],
#                 'Code': row['Code'],
#                 'Name': row['Name'],
#                 'Description': row['Description'],
#                 'Price': row['Price']
#             }
#             documents.append(Document(page_content, metadata))
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
#
#
#     print("FAISS vector store created.")
#
#     #  SERIALIZE
#     base_dir = os.path.dirname(os.path.abspath(__file__))
#     output_dir = os.path.join(base_dir, 'shopping_queries_dataset')
#     products_file = os.path.join(output_dir, 'processed_products.parquet')
#     serialized_file = os.path.join(base_dir, 'vector_index.pkl')
#     # Check if the serialized file already exists
#     if os.path.exists(serialized_file):
#         logging.info(f"Serialized file {serialized_file} already exists. Deleting it.")
#         os.remove(serialized_file)
#         logging.info(f"Deleted old version of {serialized_file}")
#
#     logging.info(f"Initializing VectorIndex instance from {products_file}")
#     vector_index_instance = vectorstore_faiss_doc.serialize_to_bytes()
#     if vector_index_instance is None:
#         raise ValueError("Failed to initialize VectorIndex instance")
#
#     logging.info("VectorIndex instance initialized")
#
#     # Serialize the VectorIndex instance to a file
#     logging.info("Starting Pickle Dump")
#     with open(serialized_file, 'wb') as file:
#         pickle.dump(vector_index_instance, file)
#         logging.info("Completed Pickle Dump")
#
#
#
#     return bedrock_embeddings, vectorstore_faiss_doc, df, llm
#
# def get_instance(cls, **kwargs):
#         """Static access method to get the singleton instance, enforcing required arguments."""
#         logging.info("Entering get_instance method")
#         if cls._instance is None:
#             logging.info("Instance is None, creating new instance")
#             pickle_file = kwargs.get('pickle_file', 'vector_index.pkl')
#             products_file = kwargs.get('products_file', '')
#
#             # Check if 'products_file' is a string
#             if not isinstance(products_file, str):
#                 logging.error("'products_file' argument must be a string")
#                 raise TypeError("'products_file' argument must be a string")
#
#             if os.path.exists(pickle_file):
#                 logging.info(f"Loading VectorIndex instance from {pickle_file}")
#                 try:
#                     with open(pickle_file, 'rb') as file:
#                         cls._instance = pickle.load(file)
#                     logging.info("VectorIndex instance loaded from pickle file.")
#                 except Exception as e:
#                     logging.error(f"Failed to load VectorIndex from pickle file: {e}")
#                     raise
#             else:
#                 logging.info("Creating new instance of VectorIndex...")
#                 cls._instance = cls(products_file=products_file)
#                 try:
#                     cls._instance.verify_or_wait_for_file_creation()
#                     cls._instance.load_processed_products()
#                     cls._instance.create_faiss_index()
#                     with open(pickle_file, 'wb') as file:
#                         pickle.dump(cls._instance, file)
#                     logging.info("VectorIndex instance created and serialized to pickle file.")
#                 except Exception as e:
#                     logging.error(f"Failed to initialize the FAISS index: {str(e)}")
#                     raise RuntimeError(f"Error initializing the FAISS index: {str(e)}")
#         else:
#             logging.info("Using existing instance of VectorIndex")
#
#         return cls._instance
