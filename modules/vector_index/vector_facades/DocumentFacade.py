from abc import ABC, abstractmethod
import pandas as pd
import os
import pickle
from concurrent.futures import ThreadPoolExecutor
import logging
import sys

from modules.vector_index.vector_utils.bedrock import BedrockClientManager
from modules.vector_index.vector_implimentations import DocumentImpl
from langchain.embeddings import BedrockEmbeddings
from langchain.vectorstores import FAISS
from langchain_aws import Bedrock


class DocumentFacade(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def initialize_embeddings_and_faiss(self):
        pass

    @abstractmethod
    def parallel_search(self, queries, vectorstore_faiss_doc, k=5, search_type="similarity", num_threads=5):
        pass