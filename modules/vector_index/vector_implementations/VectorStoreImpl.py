import re
import logging
import sys
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pandas as pd
import os
import pickle
import threading
import redis

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks.manager import (
    CallbackManagerForRetrieverRun,
    AsyncCallbackManagerForRetrieverRun,
)
from langchain_core.runnables import run_in_executor
from langchain_community.embeddings import BedrockEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_aws import Bedrock

from modules.vector_index.vector_facades.VectorStoreFacade import VectorStoreFacade
from modules.vector_index.vector_utils.bedrock import BedrockClientManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
current_dir = os.path.dirname(__file__)
faiss_creation_event = threading.Event()
tag = "VectorStoreImpl"


class VectorStoreImpl(VectorStoreFacade):
    def __init__(self, vectorstore):
        super().__init__(vectorstore)
        self.vectorstore_faiss_doc, self.exact_match_map = vectorstore

    @classmethod
    def initialize_embeddings_and_faiss(cls):
        logging.info("Initializing Bedrock clients...")
        bedrock_manager = BedrockClientManager(refresh_interval=3600)
        bedrock_runtime_client = bedrock_manager.get_bedrock_client()

        # Load or create LLM instance
        model_parameter = {
            "temperature": 0.0, "top_p": 0.5, "top_k": 250, "max_tokens_to_sample": 2000,
            "stop_sequences": ["\n\n Human: bye"]
        }
        llm = Bedrock(model_id="anthropic.claude-v2", model_kwargs=model_parameter, client=bedrock_runtime_client)

        # Initialize Titan Embeddings Model
        logging.info("Initializing Titan Embeddings Model...")
        bedrock_embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1", client=bedrock_runtime_client)
        logging.info("Titan Embeddings Model initialized.")

        # Load processed data from Parquet file
        relative_path = "../../web_extraction_tools/processed/grainger_products.parquet"
        parquet_file_path = os.path.join(current_dir, relative_path)
        parquet_file_path = os.path.abspath(parquet_file_path)
        logging.info(f"{tag} / Attempting to load file from: {parquet_file_path}")
        df = pd.read_parquet(parquet_file_path)

        # Create serialized source doc for FAISS
        documents = []
        exact_match_map = {}
        data_source_dir = os.path.join(current_dir, "../data_source")
        if not os.path.exists(data_source_dir):
            os.makedirs(data_source_dir, exist_ok=True)
        serialized_documents_file = os.path.join(data_source_dir, "documents_pickle.pkl")
        logging.info(f"{tag} / Attempting to load file from: {serialized_documents_file}")
        if os.path.exists(serialized_documents_file):
            logging.info(f"{tag} / Serialized documents file {serialized_documents_file} already exists. Loading...")
            with open(serialized_documents_file, "rb") as file:
                documents = pickle.load(file)
                logging.info("Documents file loaded successfully!")
        else:
            logging.error("Error loading serialized_documents_file at " + serialized_documents_file)
            logging.info("Generating new documents")
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

        # Store exact_match_map in Redis only if it's not empty
        if exact_match_map:
            redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
            redis_client.hmset("exact_match_map", exact_match_map)
        else:
            logging.error(f"{tag} / exact_match_map is empty and cannot be stored in Redis")

        logging.info("Structured documents created:")
        for idx, doc in enumerate(documents[:5], 1):
            logging.info(f"{tag} / Document {idx} of {len(documents)}:")
            logging.info(doc.page_content[:200])
        with open(serialized_documents_file, "wb") as file:
            pickle.dump(documents, file)

        # Ensure exact_match_map is populated when loading documents from a pickle file
        if not exact_match_map:
            for _index, doc in enumerate(documents):
                exact_match_map[doc.metadata['Code']] = _index
                exact_match_map[doc.metadata['Name']] = _index

        # Check if serialized FAISS index exists
        serialized_index_file = os.path.join(data_source_dir, "vector_index.pkl")
        logging.info(f"{tag} / Serialized index file {serialized_index_file}")
        if os.path.exists(serialized_index_file):
            logging.info(f"{tag} / Serialized file {serialized_index_file} already exists. Loading...")
            with open(serialized_index_file, "rb") as file:
                pickle_data = pickle.load(file)
                vectorstore_faiss_doc = FAISS.deserialize_from_bytes(
                    embeddings=bedrock_embeddings, serialized=pickle_data, allow_dangerous_deserialization=True
                )
            logging.info("FAISS vector store loaded from pickle file.")
        else:
            try:
                logging.info("Creating FAISS vector store from structured documents...")
                vectorstore_faiss_doc = FAISS.from_documents(documents, bedrock_embeddings)
                logging.info("FAISS vector store created.")

                # Serialize FAISS vector store to pickle file
                logging.info(f"{tag} / Serializing FAISS vector store to {serialized_index_file}")
                with open(serialized_index_file, "wb") as file:
                    serialized_vector = vectorstore_faiss_doc.serialize_to_bytes()
                    pickle.dump(serialized_vector, file)
                logging.info("FAISS vector store serialized to pickle file.")
            except Exception as e:
                logging.error(f"{tag} / Failed to create FAISS vector store: {e}")
        faiss_creation_event.set()
        first_5_items = list(exact_match_map.items())[:5]
        logging.info(f"{tag} / First 5 items of exact_match_map: {first_5_items}")
        return bedrock_embeddings, vectorstore_faiss_doc, exact_match_map, df, llm

    def parallel_search(self, queries: List[str], k: int = 5, search_type: str = "similarity", num_threads: int = 5) -> List[List[Document]]:
        logging.info("Starting parallel search")
        logging.info(f"{tag} / Queries: {queries}")
        logging.info(f"{tag} / Top k results: {k}")
        logging.info(f"{tag} / Search type: {search_type}")
        logging.info(f"{tag} / Number of threads: {num_threads}")

        def search_faiss(query: str) -> List[Document]:
            query = query.upper().strip()
            logging.info(f"{tag} / Searching for query: {query}")
            # Find all product codes that are 5-7 characters long and include at least 2 numbers and 2 letters
            product_codes = re.findall(r'\b[A-Za-z0-9]{5,7}\b', query)
            filtered_codes = [code for code in product_codes if
                              sum(c.isdigit() for c in code) >= 2 and sum(c.isalpha() for c in code) >= 2]

            logging.info(f"{tag} / Found product codes: {filtered_codes}")

            # Check for exact match first
            documents = []
            match_found = False
            for code in filtered_codes:
                if code in self.exact_match_map:
                    logging.info(f"{tag} / Exact match found for product: {code}")
                    index = self.exact_match_map[code]
                    # Get the document ID
                    doc_id = self.vectorstore_faiss_doc.index_to_docstore_id[index]
                    logging.info(f"{tag} / Document ID for exact match: {doc_id}")

                    # Retrieve the document from the docstore using the document ID
                    document = self.vectorstore_faiss_doc.docstore.search(doc_id)
                    logging.info(f"{tag} / Document retrieved for exact match: {document}")
                    documents.append(document)
                    match_found = True
            if not match_found:
                logging.info(f"{tag} / No exact match found for products. Performing FAISS search.")
                # Fallback to FAISS search
                faiss_results = self.vectorstore_faiss_doc.search(query, k=k, search_type=search_type)
                logging.info(f"{tag} / FAISS search results for query '{query}': {faiss_results}")
                return faiss_results
            else:
                return documents

        logging.info("Initializing ThreadPoolExecutor")
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            logging.info("Starting search using ThreadPoolExecutor")
            results = list(executor.map(search_faiss, queries))
        logging.info(f"{tag} / Search completed with results: {results}")
        return results
