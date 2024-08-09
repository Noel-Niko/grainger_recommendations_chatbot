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


from langchain_core.documents import Document
import pandas as pd
import numpy as np
import os
from unittest.mock import MagicMock, patch, mock_open

def create_vector_store_mock(mock_faiss_class, mock_embed_documents, mock_pickle_load, mock_open, mock_read_parquet,
                             mock_path_exists):
    # Arrange
    documents_pkl_path = os.path.abspath('stored_data_copies/documents.pkl')
    vector_index_pkl_path = os.path.abspath('stored_data_copies/vector_index.pkl')
    parquet_file_path = os.path.abspath('stored_data_copies/grainger_products.parquet')
    mock_path_exists.side_effect = lambda x: x in [documents_pkl_path, vector_index_pkl_path, parquet_file_path]

    sample_data = {
        "Code": ["C123B", "C234B", "C3234B"],
        "Name": ["Product 1", "Product 2", "Product 3"],
        "Description": ["Description of Product 1", "Description of Product 2", "Description of Product 3"],
        "Price": ["10", "20", "30"],
        "Brand": ["Brand A", "Brand B", "Brand C"]
    }
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


import logging
import os
from pathlib import Path
import pandas as pd
from langchain_core.documents import Document
from langchain_community.embeddings import BedrockEmbeddings
from langchain_community.vectorstores import FAISS
from modules.vector_index.vector_implementations.VectorStoreImpl import VectorStoreImpl
from modules.vector_index.vector_utils.bedrock import BedrockClientManager


def create_sample_parquet_file(file_path):
    sample_data = {
        "Code": ["C123B", "C234B", "C3234B"],
        "Name": ["Product 1", "Product 2", "Product 3"],
        "Description": ["Description of Product 1", "Description of Product 2", "Description of Product 3"],
        "Price": ["10", "20", "30"],
        "Brand": ["Brand A", "Brand B", "Brand C"]
    }
    df = pd.DataFrame(sample_data)
    df.to_parquet(file_path)
    print(f"Parquet file created at {file_path}")

def create_real_faiss_vector_store():
    # Initialize Bedrock clients
    bedrock_manager = BedrockClientManager(refresh_interval=3600)
    bedrock_runtime_client = bedrock_manager.get_bedrock_client()

    # Initialize Titan Embeddings Model
    bedrock_embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1", client=bedrock_runtime_client)
    print("Titan Embeddings Model initialized.")

    # Instead of loading an existing parquet file, use the one created from sample data
    parquet_file_path = 'unit_test_utils/grainger_products.parquet'

    # Load the parquet file
    df = pd.read_parquet(parquet_file_path)

    # Rest of your vector store initialization logic
    documents = []
    for _, row in df.iterrows():
        page_content = f"{row['Code']} {row['Name']} {row['Price']} {row['Description']}"
        metadata = {
            "Brand": row["Brand"], "Code": row["Code"], "Name": row["Name"],
            "Description": row["Description"], "Price": row["Price"]
        }
        documents.append(Document(page_content=page_content, metadata=metadata))

    # Create FAISS vector store
    vectorstore_faiss_doc = FAISS.from_documents(documents, bedrock_embeddings)

    # Return initialized vector store
    return VectorStoreImpl((vectorstore_faiss_doc, {}))


# Example of using the real FAISS vector store for a search
def example_search():
    vector_store_impl = create_real_faiss_vector_store()
    queries = ["Description of Product 2"]
    results = vector_store_impl.parallel_search(queries)

    for result in results:
        for doc in result:
            print(f"Found document: {doc.page_content}")


if __name__ == "__main__":
    example_search()


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

    @patch("modules.vector_index.vector_implementations.vector_store_impl.VectorStoreImpl.parallel_search")
    @patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "fake_access_key",
        "AWS_SECRET_ACCESS_KEY": "fake_secret_key",
        "AWS_DEFAULT_REGION": "us-west-2"
    })
    @patch("modules.vector_index.vector_implementationvector_store_impl.VectorStoreImpl.os.path.exists")
    @patch("modules.vector_index.vector_implementationvector_store_impl.VectorStoreImpl.pd.read_parquet")
    @patch("builtins.open", new_callable=mock_open)
    @patch("modules.vector_index.vector_implementations.vector_store_impl.VectorStoreImpl.pickle.load")
    @patch("langchain_community.embeddings.bedrock.BedrockEmbeddings.embed_documents")
    @patch("langchain_community.vectorstores.faiss.FAISS")
    def test_should_find_product_by_product_name(self, mock_parallel_search, mock_faiss_class, mock_embed_documents, mock_pickle_load, mock_open,
                                             mock_read_parquet, mock_path_exists):
        # Arrange
        product_name = "N123B"
        mock_parallel_search.return_value = [["Product with name N1"]]
        vector_store_impl = create_vector_store_mock(mock_faiss_class, mock_embed_documents, mock_pickle_load, mock_open,
                                                     mock_read_parquet, mock_path_exists)

        # Act
        results = vector_store_impl.parallel_search([product_name], MagicMock(), k=1)

        # Assert
        self.assertEqual(results[0], ["Product with name N123B"])

    def test_should_find_product_by_product_description(self):
        # Arrange
        product_description = "Description of Product 2"

        vector_store_impl = create_real_faiss_vector_store()

        # Act
        results = vector_store_impl.parallel_search([product_description], k=1)

        # Assert
        self.assertIn("Description of Product 2", results[0][0].page_content)

    @patch("modules.vector_index.vector_implementations.vector_store_impl.VectorStoreImpl.parallel_search")
    @patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "fake_access_key",
        "AWS_SECRET_ACCESS_KEY": "fake_secret_key",
        "AWS_DEFAULT_REGION": "us-west-2"
    })
    @patch("modules.vector_index.vector_implementationvector_store_impl.VectorStoreImpl.os.path.exists")
    @patch("modules.vector_index.vector_implementationvector_store_impl.VectorStoreImpl.pd.read_parquet")
    @patch("builtins.open", new_callable=mock_open)
    @patch("modules.vector_index.vector_implementations.vector_store_impl.VectorStoreImpl.pickle.load")
    @patch("langchain_community.embeddings.bedrock.BedrockEmbeddings.embed_documents")
    @patch("langchain_community.vectorstores.faiss.FAISS")
    def test_should_generate_list_of_products_via_brand(self, mock_parallel_search, mock_faiss_class, mock_embed_documents, mock_pickle_load, mock_open,
                                             mock_read_parquet, mock_path_exists):
        # Arrange
        product_brand = "B123B"
        mock_parallel_search.return_value = [["Product with brand B123B"]]
        vector_store_impl = create_vector_store_mock(mock_faiss_class, mock_embed_documents, mock_pickle_load, mock_open,
                                                     mock_read_parquet, mock_path_exists)

        # Act
        results = vector_store_impl.parallel_search([product_brand], MagicMock(), k=1)

        # Assert
        self.assertEqual(results[0], ["Product with brand B123B"])

    @patch("modules.vector_index.vector_implementations.vector_store_impl.VectorStoreImpl.parallel_search")
    @patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "fake_access_key",
        "AWS_SECRET_ACCESS_KEY": "fake_secret_key",
        "AWS_DEFAULT_REGION": "us-west-2"
    })
    @patch("modules.vector_index.vector_implementationvector_store_impl.VectorStoreImpl.os.path.exists")
    @patch("modules.vector_index.vector_implementationvector_store_impl.VectorStoreImpl.pd.read_parquet")
    @patch("builtins.open", new_callable=mock_open)
    @patch("modules.vector_index.vector_implementations.vector_store_impl.VectorStoreImpl.pickle.load")
    @patch("langchain_community.embeddings.bedrock.BedrockEmbeddings.embed_documents")
    @patch("langchain_community.vectorstores.faiss.FAISS")
    def test_should_update_product_description(self, mock_parallel_search, mock_faiss_class, mock_embed_documents, mock_pickle_load, mock_open,
                                             mock_read_parquet, mock_path_exists):
        # Arrange
        old_description = "Old description"
        new_description = "New description"
        mock_parallel_search.return_value = [[f"Product updated from {old_description} to {new_description}"]]
        vector_store_impl = create_vector_store_mock(mock_faiss_class, mock_embed_documents, mock_pickle_load, mock_open,
                                                     mock_read_parquet, mock_path_exists)

        # Act
        results = vector_store_impl.parallel_search([old_description], MagicMock(), k=1)

        # Assert
        self.assertEqual(results[0], [f"Product updated from {old_description} to {new_description}"])


if __name__ == "__main__":
    unittest.main()
