import logging
import os
import threading
import time
from typing import Optional
import unittest
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor

from modules.vector_index.document import parallel_search
import boto3
import unittest
from botocore.config import Config

import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import pickle
import pandas as pd

from modules.vector_index.vector_utils.bedrock import BedrockClientManager
from modules.vector_index.document import initialize_embeddings_and_faiss, Document

tag = "vector_document_test"


class TestInitializeEmbeddingsAndFaiss(unittest.TestCase):
    @patch("modules.vector_index.document.os.path.exists")
    @patch("modules.vector_index.document.pd.read_parquet")
    @patch("modules.vector_index.document.BedrockClientManager")
    @patch("modules.vector_index.document.open", new_callable=mock_open)
    def test_initialize_embeddings_and_faiss(self, mock_open, mock_bedrock_client_manager, mock_read_parquet,
                                             mock_path_exists):
        # Mocking the existence of files
        mock_path_exists.side_effect = lambda x: x.endswith("documents.pkl") or x.endswith("vector_index.pkl")

        # Mocking BedrockClientManager
        mock_bedrock_client_manager.return_value.get_bedrock_client.return_value = MagicMock()

        # Mocking pandas read_parquet
        mock_df = pd.DataFrame({
            "Code": ["C1", "C2"],
            "Name": ["N1", "N2"],
            "Description": ["D1", "D2"],
            "Price": ["P1", "P2"],
            "Brand": ["B1", "B2"]
        })
        mock_read_parquet.return_value = mock_df

        # Mocking the open function for pickle.load
        mock_open.return_value = MagicMock(spec=pickle.load)
        mock_open.return_value.__enter__.return_value = MagicMock(spec=pickle.load)
        mock_open.return_value.__enter__.return_value.read.return_value = b"mock_pickle_data"

        # Call the function
        bedrock_embeddings, vectorstore_faiss_doc, df, llm = initialize_embeddings_and_faiss()

        # Assert statements to check if the function works as expected
        self.assertIsNotNone(bedrock_embeddings)
        self.assertIsNotNone(vectorstore_faiss_doc)
        self.assertIsNotNone(df)
        self.assertIsNotNone(llm)
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]["Code"], "C1")


class TestParallelSearch(unittest.TestCase):

    @patch("your_module.ThreadPoolExecutor")
    def test_parallel_search(self, mock_thread_pool_executor):
        # Mocking FAISS vector store
        mock_faiss_vectorstore = MagicMock()
        mock_faiss_vectorstore.search.return_value = ["result1", "result2"]

        # Mocking ThreadPoolExecutor
        mock_executor_instance = mock_thread_pool_executor.return_value
        mock_executor_instance.map.return_value = [["result1"], ["result2"]]

        # Call the function
        queries = ["query1", "query2"]
        results = parallel_search(queries, mock_faiss_vectorstore, k=2, search_type="similarity", num_threads=2)

        # Assert statements to check if the function works as expected
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], ["result1"])
        self.assertEqual(results[1], ["result2"])


if __name__ == "__main__":
    unittest.main()


class VectorDocumentTest():

    def should_find_product_by_product_code(self, product_code):
        pass

    def should_find_product_by_product_name(self, product_name):
        pass

    def should_find_product_by_product_description(self, product_email):
        pass

    def should_generate_list_of_products_via_brand(self, product_email):
        pass

    def should_update_product_description(self):
        pass


if __name__ == "__main__":
    unittest.main()
