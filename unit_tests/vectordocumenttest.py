import json
import os
import pickle
import unittest
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd

from modules.vector_index.document import initialize_embeddings_and_faiss, Document, parallel_search


class TestInitializeEmbeddingsAndFaiss(unittest.TestCase):

    @patch("modules.vector_index.document.os.path.exists")
    @patch("modules.vector_index.document.pd.read_parquet")
    @patch("modules.vector_index.document.BedrockClientManager")
    @patch("builtins.open", new_callable=mock_open)
    @patch("modules.vector_index.document.pickle.load")
    def test_initialize_embeddings_and_faiss(self, mock_pickle_load, mock_open, mock_bedrock_client_manager, mock_read_parquet, mock_path_exists):
        # Arrange
        documents_pkl_path = os.path.abspath('stored_data_copies/documents.pkl')
        vector_index_pkl_path = os.path.abspath('stored_data_copies/vector_index.pkl')
        parquet_file_path = os.path.abspath('stored_data_copies/grainger_products.parquet')

        mock_path_exists.side_effect = lambda x: x in [documents_pkl_path, vector_index_pkl_path, parquet_file_path]

        # Mocking BedrockClientManager
        mock_bedrock_client = MagicMock()
        mock_bedrock_client_manager.return_value.get_bedrock_client.return_value = mock_bedrock_client

        # Mocking pandas read_parquet to return a specific DataFrame
        mock_df = pd.DataFrame({
            "Code": ["C1", "C2"],
            "Name": ["N1", "N2"],
            "Description": ["D1", "D2"],
            "Price": ["P1", "P2"],
            "Brand": ["B1", "B2"]
        })
        mock_read_parquet.return_value = mock_df

        def load_actual_pickle_data(file_path):
            with open(file_path, "rb") as f:
                return pickle.load(f)

        def mock_pickle_load_side_effect(file):
            if file.name == documents_pkl_path:
                return load_actual_pickle_data(documents_pkl_path)
            elif file.name == vector_index_pkl_path:
                return load_actual_pickle_data(vector_index_pkl_path)

        mock_pickle_load.side_effect = mock_pickle_load_side_effect

        def mock_invoke_model(body, modelId, accept, contentType):
            mock_response = MagicMock()
            mock_response.get.return_value.read.return_value = json.dumps({
                "embedding": [0.1, 0.2, 0.3, 0.4]
            }).encode('utf-8')
            return mock_response

        mock_bedrock_client.invoke_model.side_effect = mock_invoke_model

        # Act
        bedrock_embeddings, vectorstore_faiss_doc, df, llm = initialize_embeddings_and_faiss()

        # Assert
        self.assertIsNotNone(bedrock_embeddings)
        self.assertIsNotNone(vectorstore_faiss_doc)
        self.assertIsNotNone(df)
        self.assertIsNotNone(llm)
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]["Code"], "C1")


class TestParallelSearch(unittest.TestCase):

    @patch("concurrent.futures.ThreadPoolExecutor")
    def test_parallel_search(self, mock_thread_pool_executor):
        # Arrange
        mock_faiss_vectorstore = MagicMock()
        mock_faiss_vectorstore.search.return_value = ["result1", "result2"]
        # Act
        queries = ["query1", "query2"]
        results = parallel_search(queries, mock_faiss_vectorstore, k=2, search_type="similarity", num_threads=2)

        # Assert
        self.assertEqual(len(results), 2)
        self.assertIn("result1", results[0])
        self.assertIn("result2", results[0])
        self.assertIn("result1", results[1])
        self.assertIn("result2", results[1])

if __name__ == "__main__":
    unittest.main()




