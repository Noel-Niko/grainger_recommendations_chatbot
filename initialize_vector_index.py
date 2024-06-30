import logging
import os
import pickle
from vector_index import Document
from bedrock_initializer import check_and_initialize_llm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
base_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(base_dir, 'processed')
products_file = os.path.join(output_dir, 'grainger_products.parquet')
serialized_file = os.path.join(base_dir, 'vector_index.pkl')  # Store at the root level



try:
    logging.info(f"Starting initialization process.")
    logging.info("Setting up LLM")
    check_and_initialize_llm()
    # Ensure output directory exists
    # if not os.path.exists(output_dir):
    #     os.makedirs(output_dir)
    #     logging.info(f"Created directory {output_dir}")
    #
    # # Check if the serialized file already exists
    # if os.path.exists(serialized_file):
    #     logging.info(f"Serialized file {serialized_file} already exists. Deleting it.")
    #     os.remove(serialized_file)
    #     logging.info(f"Deleted old version of {serialized_file}")

    logging.info(f"Initializing VectorIndex instance from {products_file}")
    #
    # vector_index_instance = Document.get_instance(products_file=products_file)
    # if vector_index_instance is None:
    #     raise ValueError("Failed to initialize VectorIndex instance")
    #
    # logging.info("VectorIndex instance initialized")
    #
    # # Serialize the VectorIndex instance to a file
    # logging.info("Starting Pickle Dump")
    # with open(serialized_file, 'wb') as file:
    #     pickle.dump(vector_index_instance, file)
    #     logging.info("Completed Pickle Dump")

except Exception as e:
    logging.error(f"Exception occurred during initialization or serialization: {e}")
