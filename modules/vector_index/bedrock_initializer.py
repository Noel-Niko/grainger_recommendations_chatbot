import logging
from langchain_aws import BedrockLLM
from langchain.llms.bedrock import Bedrock
import json
import os
import sys
import boto3
import botocore
from IPython.display import Image
from .utils import bedrock, print_ww


class LLMInitializer:
    _instance = None
    bedrock_runtime = None
    llm = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMInitializer, cls).__new__(cls)
        return cls._instance

    def check_and_initialize_llm(self):
        try:
            logging.info("Checking if 'llm' is defined...")
            if self.llm is None:
                module_path = "../../.."
                sys.path.append(os.path.abspath(module_path))

                os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

                logging.info("Getting bedrock client...")
                boto3_bedrock = bedrock.get_bedrock_client(
                    assumed_role=os.environ.get("BEDROCK_ASSUME_ROLE", None),
                    region=os.environ.get("AWS_DEFAULT_REGION", None),
                    runtime=False)

                self.bedrock_runtime = bedrock.get_bedrock_client(
                    assumed_role=os.environ.get("BEDROCK_ASSUME_ROLE", None),
                    region=os.environ.get("AWS_DEFAULT_REGION", None))

                model_parameter = {
                    "temperature": 0.0,
                    "top_p": .5,
                    "top_k": 250,
                    "max_tokens_to_sample": 2000,
                    "stop_sequences": ["\n\n Human: bye"]
                }

                logging.info("Initializing Bedrock...")
                self.llm = Bedrock(
                    model_id="anthropic.claude-v2",
                    model_kwargs=model_parameter,
                    client=self.bedrock_runtime
                )
            logging.info("'llm' initialized successfully.")
            return self.llm, self.bedrock_runtime
        except Exception as e:
            logging.error(f"Error initializing LLM: {str(e)}")
            raise e
