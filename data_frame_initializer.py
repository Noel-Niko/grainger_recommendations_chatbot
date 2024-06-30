import pandas as pd
import os

class DataFrameSingleton:
    _instance = None
    _df = None

    @classmethod
    def get_instance(cls, parquet_file_path="processed/grainger_products.parquet"):
        if cls._instance is None:
            cls._instance = cls()
            root_dir = os.path.dirname(os.path.abspath(__file__))
            absolute_path = os.path.join(root_dir, parquet_file_path)
            cls._load_dataframe(absolute_path)
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