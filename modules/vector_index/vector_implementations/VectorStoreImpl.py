# modules/vector_index/vector_implementations/VectorStoreImpl.py
from concurrent.futures import ThreadPoolExecutor

from modules.vector_index.vector_facades.VectorStoreFacade import VectorStoreFacade
from modules.vector_index.vector_utils.bedrock import BedrockClientManager
from modules.vector_index.vector_implementations.Document import Document
from langchain_community.embeddings import BedrockEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_aws import Bedrock
import pandas as pd
import os
import pickle
import logging
import threading


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

        data_source_dir = os.path.join(current_dir, "data_sources")
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
        logging.info("Structured documents created:")
        for idx, doc in enumerate(documents[:5], 1):
            logging.info(f"{tag} / Document {idx} of {len(documents)}:")
            logging.info(doc.page_content[:200])
        with open(serialized_documents_file, "wb") as file:
            pickle.dump(documents, file)

        # Check if serialized FAISS index exists
        serialized_index_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                             "data_sources/vector_index.pkl")
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
        return bedrock_embeddings, vectorstore_faiss_doc, df, llm

    def parallel_search(self, queries, k=5, search_type="similarity", num_threads=5):
        def search_faiss(query):
            # Check for exact match first
            if query in self.exact_match_map:
                index = self.exact_match_map[query]
                # Get the document ID
                doc_id = self.vectorstore_faiss_doc.index_to_docstore_id[index]

                # Retrieve the document from the docstore using the document ID
                document = self.vectorstore_faiss_doc.docstore.search(doc_id)

                return [document]
            else:
                # Fallback to FAISS search
                return self.vectorstore_faiss_doc.search(query, k=k, search_type=search_type)

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            results = list(executor.map(search_faiss, queries))
        return results

