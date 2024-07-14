import logging
import os
import pickle
import sys
from concurrent.futures import ThreadPoolExecutor

import boto3
import pandas as pd
from langchain.embeddings import BedrockEmbeddings
from langchain.vectorstores import FAISS
from langchain_aws import Bedrock

from .bedrock_initializer import bedrock

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)


class Document:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata


def get_boto3_session():
    role_arn = os.environ.get("BEDROCK_ASSUME_ROLE")
    if not role_arn:
        logging.error("Environment variable 'BEDROCK_ASSUME_ROLE' is not set")
        raise ValueError("Environment variable 'BEDROCK_ASSUME_ROLE' is not set")

    try:
        session = boto3.Session()
        sts_client = session.client('sts')

        assume_role_object = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName="AssumeRoleSession1"
        )
        credentials = assume_role_object['Credentials']
        return boto3.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken']
        )
    except Exception as e:
        logging.error(f"Error assuming role: {str(e)}")
        raise


def initialize_embeddings_and_faiss():
    boto3_session = get_boto3_session()

    logging.info("Initializing Bedrock clients...")
    bedrock_runtime_client = boto3_session.client('bedrock-runtime')

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
        client=bedrock_runtime_client
    )

    # Initialize Titan Embeddings Model
    logging.info("Initializing Titan Embeddings Model...")
    bedrock_embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1", client=bedrock_runtime_client)
    logging.info("Titan Embeddings Model initialized.")

    # Load processed data from Parquet file
    relative_path = '../web_extraction_tools/processed/grainger_products.parquet'
    parquet_file_path = os.path.join(current_dir, relative_path)
    parquet_file_path = os.path.abspath(parquet_file_path)
    logging.info(f"Attempting to load file from: {parquet_file_path}")
    df = pd.read_parquet(parquet_file_path)

    # Create serialized source doc for FAISS
    documents = []
    data_source_dir = os.path.join(current_dir, 'data_source')
    os.makedirs(data_source_dir, exist_ok=True)
    serialized_documents_file = os.path.join(data_source_dir, 'documents.pkl')
    logging.info(f"Attempting to load file from: {serialized_documents_file}")
    if os.path.exists(serialized_documents_file):
        logging.info(f"Serialized documents file {serialized_documents_file} already exists. Loading...")
        with open(serialized_documents_file, 'rb') as file:
            documents = pickle.load(file)
            logging.info("Documents file loaded successfully!")
    else:
        logging.error("Error loading serialized_documents_file at " + serialized_documents_file)
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
    pickle.dump(documents, open(serialized_documents_file, "wb"))

    # Check if serialized FAISS index exists
    serialized_index_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vector_index.pkl')
    logging.info(f"Serialized index file {serialized_index_file}")
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

# 'similarity' is standard 'mmr' for greater variety
def parallel_search(queries, vectorstore_faiss_doc, k=5, search_type='similarity', num_threads=5):
    def search_faiss(query):
        return vectorstore_faiss_doc.search(query, k=k, search_type=search_type)

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        results = list(executor.map(search_faiss, queries))
    return results
