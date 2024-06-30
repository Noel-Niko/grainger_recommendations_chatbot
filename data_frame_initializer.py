import pandas as pd
import os

class DataFrameSingleton:
    _instance = None
    _df = None

    @classmethod
    def get_instance(cls, parquet_file_path="/Users/noel_niko/PycharmProjects/graigner_recommendations_chatbot/processed/grainger_products.parquet"):
        if cls._instance is None:
            cls._instance = cls()
            cls._load_dataframe(parquet_file_path)
        return cls._instance

    @classmethod
    def _load_dataframe(cls, parquet_file_path):
        print("Attempting to load file from:", parquet_file_path)
        try:
            cls._df = pd.read_parquet(parquet_file_path)
            print("File loaded successfully!")
        except FileNotFoundError as e:
            print("Error loading file:", e)

    @property
    def df(self):
        return self._df