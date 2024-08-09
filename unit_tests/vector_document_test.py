import pickle
import unittest
from unittest.mock import mock_open

from langchain_community.embeddings import BedrockEmbeddings

from modules.vector_index.vector_implementations import VectorStoreImpl
from modules.vector_index.vector_implementations.VectorStoreImpl import VectorStoreImpl
from modules.vector_index.vector_utils.bedrock import BedrockClientManager


class TestVectorStoreImpl(unittest.TestCase):
    vectorstore_faiss_doc = None
    vectorstore_impl = None

    @classmethod
    def setUpClass(cls):

        # Initialize vector store with sample data
        cls.vectorstore_impl = create_real_faiss_vector_store()

    def test_should_find_product_with_matching_full_input(self):
        # Arrange
        product_code = "C1234B Product 1 10 About Prod 1"

        # Act
        results = self.vectorstore_impl.parallel_search([product_code], k=1)

        # Assert
        expected_page_content = "Product 1"
        self.assertIn(expected_page_content, results[0][0].page_content)

    def test_should_find_product_by_product_code(self):
        # Arrange
        product_code = "C234B"
        vector_store_impl = create_real_faiss_vector_store()
        # Act
        results = vector_store_impl.parallel_search([product_code], k=1)

        # Assert
        self.assertIn(product_code, results[0][0].page_content)


if __name__ == "__main__":
    unittest.main()

import unittest
from langchain_community.vectorstores import FAISS


from langchain_core.documents import Document
import pandas as pd
import numpy as np
import os
from unittest.mock import MagicMock, patch, mock_open

sample_data = {
        "Code": ["C123B", "C234B", "C3234B"],
        "Name": ["Product 1", "Item 2", "C Thing"],
        "Description": ["About Prod 1", "Item 2 Described", "Tool 3 Characteristics"],
        "Price": ["$10.00", "$20.00", "$30.00"],
        "Brand": ["Manufacturer A", "Brand B1", "C Distributor"]
    }

def create_vector_store_mock(mock_faiss_class, mock_embed_documents, mock_pickle_load, mock_open, mock_read_parquet,
                             mock_path_exists):
    # Arrange
    documents_pkl_path = os.path.abspath('stored_data_copies/documents.pkl')
    vector_index_pkl_path = os.path.abspath('stored_data_copies/vector_index.pkl')
    parquet_file_path = os.path.abspath('stored_data_copies/grainger_products.parquet')
    mock_path_exists.side_effect = lambda x: x in [documents_pkl_path, vector_index_pkl_path, parquet_file_path]

    mock_df = pd.DataFrame(sample_data)
    mock_read_parquet.return_value = mock_df

    # Mocking pickle.load
    def load_actual_pickle_data(file_path):
        with open(file_path, "rb") as f:
            return pickle.load(f)

    def mock_pickle_load_side_effect(file):
        if file.name == documents_pkl_path:
            return load_actual_pickle_data(documents_pkl_path)
        elif file.name == vector_index_pkl_path:
            return load_actual_pickle_data(vector_index_pkl_path)

    mock_pickle_load.side_effect = mock_pickle_load_side_effect

    # Mock the Bedrock embeddings
    mock_embed_documents.return_value = np.array([
        [0.1, 0.2, 0.3, 0.4],
        [0.5, 0.6, 0.7, 0.8],
        [0.9, 1.0, 1.1, 1.2]
    ], dtype=np.float32)

    # Create a mock FAISS object and exact_match_map
    mock_faiss = MagicMock()
    mock_faiss_class.from_documents.return_value = mock_faiss
    exact_match_map = {"C123B": 0, "C234B": 1, "C345B": 2}

    # Convert mock_df rows to Document objects
    documents = []
    for _, row in mock_df.iterrows():
        page_content = f"{row['Code']} {row['Name']} {row['Price']} {row['Description']}"
        metadata = {
            "Brand": row["Brand"], "Code": row["Code"], "Name": row["Name"],
            "Description": row["Description"], "Price": row["Price"]
        }
        documents.append(Document(page_content=page_content, metadata=metadata))

    # Set up the mock search method to return the appropriate Document objects
    # mock_faiss.search.return_value = documents

    # Mock the vector_store to return a tuple as expected
    vector_store = (mock_faiss, exact_match_map)

    # Act
    return VectorStoreImpl(vector_store)


def create_sample_parquet_file():
    df = pd.DataFrame(sample_data)
    df.to_parquet('unit_test_utils/grainger_products.parquet')

def create_real_faiss_vector_store():
    # Initialize Bedrock clients
    bedrock_manager = BedrockClientManager(refresh_interval=3600)
    bedrock_runtime_client = bedrock_manager.get_bedrock_client()

    # Initialize Titan Embeddings Model
    bedrock_embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1", client=bedrock_runtime_client)
    print("Titan Embeddings Model initialized.")

    # Instead of loading an existing parquet file, use the one created from sample data
    create_sample_parquet_file()
    parquet_file_path = 'unit_test_utils/grainger_products.parquet'

    # Load the parquet file
    df = pd.read_parquet(parquet_file_path)

    # Rest of your vector store initialization logic
    documents = []
    exact_match_map = {}
    for _index, row in df.iterrows():
        page_content = f"{row['Code']} {row['Brand']} {row['Name']} {row['Price']} {row['Description']}"
        metadata = {
            "Brand": row["Brand"], "Code": row["Code"], "Name": row["Name"],
            "Description": row["Description"], "Price": row["Price"]
        }
        # Populate exact match map
        exact_match_map[row['Code']] = _index
        exact_match_map[row['Name']] = _index
        documents.append(Document(page_content=page_content, metadata=metadata))

    # Create FAISS vector store
    vectorstore_faiss_doc = FAISS.from_documents(documents, bedrock_embeddings)

    # Return initialized vector store
    return VectorStoreImpl((vectorstore_faiss_doc, exact_match_map))

class TestInitializeEmbeddingsAndFaiss(unittest.TestCase):

    @patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "fake_access_key",
        "AWS_SECRET_ACCESS_KEY": "fake_secret_key",
        "AWS_DEFAULT_REGION": "us-west-2"
    })
    @patch("modules.vector_index.vector_implementations.VectorStoreImpl.os.path.exists")
    @patch("modules.vector_index.vector_implementations.VectorStoreImpl.pd.read_parquet")
    @patch("builtins.open", new_callable=mock_open)
    @patch("modules.vector_index.vector_implementations.VectorStoreImpl.pickle.load")
    @patch("langchain_community.embeddings.bedrock.BedrockEmbeddings.embed_documents")
    @patch("langchain_community.vectorstores.faiss.FAISS")
    def test_initialize_embeddings_and_faiss(self, mock_faiss_class, mock_embed_documents, mock_pickle_load, mock_open,
                                             mock_read_parquet, mock_path_exists):
        # Arrange
        vector_store_impl = create_vector_store_mock(mock_faiss_class, mock_embed_documents, mock_pickle_load, mock_open,
                                                     mock_read_parquet, mock_path_exists)

        # Act
        bedrock_embeddings, vectorstore_faiss_doc, exact_match_map, df, llm = vector_store_impl.initialize_embeddings_and_faiss()

        # Assert
        self.assertIsNotNone(bedrock_embeddings)
        self.assertIsNotNone(vectorstore_faiss_doc)
        self.assertIsNotNone(df)
        self.assertIsNotNone(llm)
        self.assertIsNotNone(exact_match_map)
        self.assertEqual(len(df), 3)
        self.assertEqual(df.iloc[0]["Code"], "C123B")


if __name__ == "__main__":
    unittest.main()


class TestParallelSearch(unittest.TestCase):

    @patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "fake_access_key",
        "AWS_SECRET_ACCESS_KEY": "fake_secret_key",
        "AWS_DEFAULT_REGION": "us-west-2"
    })
    @patch("modules.vector_index.vector_implementations.VectorStoreImpl.os.path.exists")
    @patch("modules.vector_index.vector_implementations.VectorStoreImpl.pd.read_parquet")
    @patch("builtins.open", new_callable=mock_open)
    @patch("modules.vector_index.vector_implementations.VectorStoreImpl.pickle.load")
    @patch("langchain_community.embeddings.bedrock.BedrockEmbeddings.embed_documents")
    @patch("langchain_community.vectorstores.faiss.FAISS")
    def test_parallel_search(self, mock_faiss_class, mock_embed_documents, mock_pickle_load, mock_open,
                                             mock_read_parquet, mock_path_exists):
        # Arrange
        vector_store_impl = create_vector_store_mock(mock_faiss_class, mock_embed_documents, mock_pickle_load, mock_open,
                                                     mock_read_parquet, mock_path_exists)
        # Arrange
        mock_faiss_class.from_documents.return_value.search.return_value = [
            ["result1", "result2"],
            ["result1", "result2"]
        ]

        # Act
        queries = ["query1", "query2"]
        results = vector_store_impl.parallel_search(queries, k=2, search_type="similarity", num_threads=2)

        # Assert
        self.assertEqual(len(results), 2)
        self.assertIn("result1", results[0][0])
        self.assertIn("result2", results[0][0])
        self.assertIn("result1", results[1][0])
        self.assertIn("result2", results[1][0])


class VectorDocumentTest(unittest.TestCase):
    vectorstore_faiss_doc = None
    vectorstore_impl = None

    @classmethod
    def setUpClass(cls):
        # Initialize vector store with sample data
        cls.vectorstore_impl = create_real_faiss_vector_store()

    def test_should_find_product_by_product_code(self):
        # Arrange
        product_code = "C123B"
        vector_store_impl = create_real_faiss_vector_store()

        # Act
        results = vector_store_impl.parallel_search([product_code], k=1)

        # Assert
        self.assertIn("Product 1", results[0][0].page_content)

    def test_should_find_product_by_product_name(self,):
        # Arrange
        product_name = "Item 2"

        vector_store_impl = create_real_faiss_vector_store()

        # Act
        results = vector_store_impl.parallel_search([product_name], k=1)

        # Assert
        self.assertIn("Item 2 Described", results[0][0].page_content)

    def test_should_find_product_by_product_description(self):
        # Arrange
        product_description = "Tool 3 Characteristics"

        vector_store_impl = create_real_faiss_vector_store()

        # Act
        results = vector_store_impl.parallel_search([product_description], k=1)

        # Assert
        self.assertIn("C3234B", results[0][0].page_content)
        self.assertIn(product_description, results[0][0].page_content)


    def test_should_generate_list_of_products_via_brand(self):
        # Arrange
        product_brand = "Brand B1"
        vector_store_impl = create_real_faiss_vector_store()

        # Act
        results = vector_store_impl.parallel_search([product_brand], k=1)

        # Assert
        self.assertIn("Item 2 Described", results[0][0].page_content)


if __name__ == "__main__":
    unittest.main()
