# import pandas as pd
# import os
# import logging
#
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
#
#
# class DataFrameSingleton:
#     _instance = None
#
#     def __init__(self):
#         self._df = None
#
#     @classmethod
#     def get_instance(cls, parquet_file_path="modules/vector_index/processed/grainger_products.parquet"):
#         logging.info("Entering dataframe get_instance method")
#         if cls._instance is None:
#             try:
#                 logging.info("Loading new dataframe instance...")
#                 cls._instance = cls()
#                 absolute_path = cls._generate_absolute_path(parquet_file_path)
#                 cls._instance._load_dataframe(absolute_path)
#                 logging.info("Dataframe loaded successfully!")
#             except Exception as e:
#                 logging.error(f"Error loading dataframe: {e}")
#         return cls._instance
#
#     @classmethod
#     def _generate_absolute_path(cls, relative_path):
#         root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
#         absolute_path = os.path.join(root_dir, relative_path)
#         return absolute_path
#
#     def _load_dataframe(self, parquet_file_path):
#         print("Attempting to load file from:", parquet_file_path)
#         try:
#             self._df = pd.read_parquet(parquet_file_path)
#             # TODO: TAKE SAMPLE
#             self._df = self._df #.sample(frac=0.1)
#             print("File loaded successfully!")
#         except FileNotFoundError as e:
#             print("Error loading file:", e)
#
#     @property
#     def df(self):
#         return self._df