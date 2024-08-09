import json
import os
import pickle
import unittest
from unittest.mock import patch, MagicMock, mock_open

import numpy as np
import pandas as pd

from modules.vector_index.vector_implementations import VectorStoreImpl
from modules.vector_index.vector_implementations.VectorStoreImpl import VectorStoreImpl
from unit_tests.unit_test_utils.sample_vector_store import initialize_vector_store_with_sample_data, \
    return_sample_vector


class TestVectorStoreImpl(unittest.TestCase):
    vectorstore_faiss_doc = None
    vectorstore_impl = None

    @classmethod
    def setUpClass(cls):
        df = return_sample_vector()
        # Initialize vector store with sample data
        cls.vectorstore_faiss_doc = initialize_vector_store_with_sample_data(df)
        cls.vectorstore_impl = VectorStoreImpl(cls.vectorstore_faiss_doc)

    def test_should_find_product_with_matching_full_input(self):
        # Arrange
        product_code = "C1234B Product 1 10 Description of Product 1"

        # Act
        results = self.vectorstore_impl.parallel_search([product_code], k=1)

        # Assert
        expected_page_content = "Product 1"
        self.assertIn(expected_page_content, results[0][0].page_content)

    def test_should_find_product_by_product_code(self):
        # Arrange
        product_code = "Product 3"

        # Act
        results = self.vectorstore_impl.parallel_search([product_code], k=1)

        # Assert
        expected_page_content = "Product 3"
        self.assertIn(expected_page_content, results[0][0].page_content)


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import MagicMock, patch, mock_open
import os
import pandas as pd
import numpy as np
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS


class TestInitializeEmbeddingsAndFaiss(unittest.TestCase):

    @patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "fake_access_key",
        "AWS_SECRET_ACCESS_KEY": "fake_secret_key",
        "AWS_DEFAULT_REGION": "us-west-2"
    })
    @patch("modules.vector_index.vector_implementations.VectorStoreImpl.os.path.exists")
    @patch("modules.vector_index.vector_implementations.VectorStoreImpl.pd.read_parquet")
    @patch("modules.vector_index.vector_implementations.VectorStoreImpl.BedrockClientManager")
    @patch("builtins.open", new_callable=mock_open)
    @patch("modules.vector_index.vector_implementations.VectorStoreImpl.pickle.load")
    @patch("langchain_community.embeddings.bedrock.BedrockEmbeddings.embed_documents")
    @patch("langchain_community.vectorstores.faiss.FAISS")
    def test_initialize_embeddings_and_faiss(self, mock_faiss_class, mock_embed_documents, mock_pickle_load, mock_open,
                                             mock_bedrock_client_manager, mock_read_parquet,
                                             mock_path_exists):
        # Arrange
        documents_pkl_path = os.path.abspath('stored_data_copies/documents.pkl')
        vector_index_pkl_path = os.path.abspath('stored_data_copies/vector_index.pkl')
        parquet_file_path = os.path.abspath('stored_data_copies/grainger_products.parquet')

        mock_path_exists.side_effect = lambda x: x in [documents_pkl_path, vector_index_pkl_path, parquet_file_path]

        # Mocking pandas read_parquet to return a specific DataFrame
        mock_df = pd.DataFrame({
            "Code": ["C123B", "C234B", "C345B"],
            "Name": ["N123B", "N223B", "N323B"],
            "Description": ["D123B", "D223B", "D323B"],
            "Price": ["P123B", "P223B", "P323B"],
            "Brand": ["B123B", "B223B", "B323B"]
        })
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

        # Mock the Bedrock embeddings to return the correct number of embeddings
        mock_embed_documents.return_value = np.array([
            [0.1, 0.2, 0.3, 0.4],
            [0.5, 0.6, 0.7, 0.8],
            [0.9, 1.0, 1.1, 1.2]
        ], dtype=np.float32)

        # Create a mock FAISS object and exact_match_map
        mock_faiss = MagicMock()
        mock_faiss_class.from_documents.return_value = mock_faiss
        exact_match_map = {"C123B": 0, "C234B": 1, "C345B": 2}

        # Mock the vector_store to return a tuple as expected
        vector_store = (mock_faiss, exact_match_map)

        # Act
        vector_store_impl = VectorStoreImpl(vector_store)
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

    @patch("concurrent.futures.ThreadPoolExecutor")
    def test_parallel_search(self, mock_thread_pool_executor):
        # Arrange
        mock_faiss_vectorstore = MagicMock()
        mock_faiss_vectorstore.search.return_value = ["result1", "result2"]
        vector_store_impl = VectorStoreImpl(mock_faiss_vectorstore)
        # Act
        queries = ["query1", "query2"]
        results = vector_store_impl.parallel_search(queries, k=2, search_type="similarity", num_threads=2)

        # Assert
        self.assertEqual(len(results), 2)
        self.assertIn("result1", results[0])
        self.assertIn("result2", results[0])
        self.assertIn("result1", results[1])
        self.assertIn("result2", results[1])


class VectorDocumentTest(unittest.TestCase):
    vectorstore_faiss_doc = None
    vectorstore_impl = None

    @classmethod
    def setUpClass(cls):
        # Initialize vector store with sample data
        df = return_sample_vector()
        cls.vectorstore_faiss_doc = initialize_vector_store_with_sample_data(df)
        cls.vectorstore_impl = VectorStoreImpl(cls.vectorstore_faiss_doc)

    def test_should_find_product_by_product_code(self):
        # Arrange
        product_code = "C123B"

        # Act
        results = self.vectorstore_impl.parallel_search([product_code], k=1)

        # Assert
        self.assertIn("Product 1", results[0][0].page_content)

    @patch("modules.vector_index.vector_implementations.VectorStoreImpl.parallel_search")
    def test_should_find_product_by_product_name(self, mock_parallel_search):
        # Arrange
        product_name = "N123B"
        mock_parallel_search.return_value = [["Product with name N1"]]
        vector_store_impl = VectorStoreImpl(MagicMock())

        # Act
        results = vector_store_impl.parallel_search([product_name], MagicMock(), k=1)

        # Assert
        self.assertEqual(results[0], ["Product with name N123B"])

    @patch("modules.vector_index.vector_implementations.VectorStoreImpl.parallel_search")
    def test_should_find_product_by_product_description(self, mock_parallel_search):
        # Arrange
        product_description = "D123B"
        mock_parallel_search.return_value = [["Product with description D123B"]]
        vector_store_impl = VectorStoreImpl(MagicMock())

        # Act
        results = vector_store_impl.parallel_search([product_description], MagicMock(), k=1)

        # Assert
        self.assertEqual(results[0], ["Product with description D123B"])

    @patch("modules.vector_index.vector_implementations.VectorStoreImpl.parallel_search")
    def test_should_generate_list_of_products_via_brand(self, mock_parallel_search):
        # Arrange
        product_brand = "B123B"
        mock_parallel_search.return_value = [["Product with brand B123B"]]
        vector_store_impl = VectorStoreImpl(MagicMock())

        # Act
        results = vector_store_impl.parallel_search([product_brand], MagicMock(), k=1)

        # Assert
        self.assertEqual(results[0], ["Product with brand B123B"])

    @patch("modules.vector_index.vector_implementations.VectorStoreImpl.parallel_search")
    def test_should_update_product_description(self, mock_parallel_search):
        # Arrange
        old_description = "Old description"
        new_description = "New description"
        mock_parallel_search.return_value = [[f"Product updated from {old_description} to {new_description}"]]
        vector_store_impl = VectorStoreImpl(MagicMock())

        # Act
        results = vector_store_impl.parallel_search([old_description], MagicMock(), k=1)

        # Assert
        self.assertEqual(results[0], [f"Product updated from {old_description} to {new_description}"])


if __name__ == "__main__":
    unittest.main()
