import pandas as pd
import os
import pickle
import logging
from langchain.embeddings import BedrockEmbeddings
from langchain.vectorstores import FAISS
from langchain_core.documents import Document

import pandas as pd

from modules.vector_index.vector_utils.bedrock import BedrockClientManager

sample_data = {
    "Code": ["C123B", "C234B", "C3234B"],
    "Name": ["Product 1", "Product 2", "Product 3"],
    "Description": ["Description of Product 1", "Description of Product 2", "Description of Product 3"],
    "Price": ["10", "20", "30"],
    "Brand": ["Brand A", "Brand B", "Brand C"]
}

def return_sample_vector():
    # Preprocess to extract code and product name for exact matching
    sample_df = pd.DataFrame(sample_data)
    sample_df['Code'] = sample_df['Code'].astype(str)
    sample_df['ProductName'] = sample_df['Name'].str.extract('(\w+)').fillna('').astype(str)
    return sample_df


def initialize_vector_store_with_sample_data(df):
    logging.info("Initializing Bedrock clients...")
    bedrock_manager = BedrockClientManager(refresh_interval=3600)
    bedrock_runtime_client = bedrock_manager.get_bedrock_client()

    # Load or create LLM instance
    # Initialize Titan Embeddings Model
    logging.info("Initializing Titan Embeddings Model...")
    bedrock_embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1", client=bedrock_runtime_client)
    logging.info("Titan Embeddings Model initialized.")

    documents = []
    exact_match_map = {}  # Map for exact matching

    for _index, row in df.iterrows():
        description = row["Description"] if pd.notna(row["Description"]) else ""
        price = row["Price"] if pd.notna(row["Price"]) else ""
        normalized_name = row['Name'].strip()
        normalized_price = price.strip() if price else ""
        page_content = f"{row['Code']} {normalized_name} {normalized_price} {description}"

        metadata = {
            "Brand": row["Brand"], "Code": row["Code"], "Name": row["Name"],
            "Description": row["Description"], "Price": row["Price"]
        }

        doc = Document(page_content=page_content, metadata=metadata)
        documents.append(doc)

        # Populate exact match map
        exact_match_map[row['Code']] = _index
        exact_match_map[row['Name']] = _index

    # Create FAISS vector store from documents
    vectorstore_faiss_doc = FAISS.from_documents(documents, bedrock_embeddings)

    return vectorstore_faiss_doc, exact_match_map
