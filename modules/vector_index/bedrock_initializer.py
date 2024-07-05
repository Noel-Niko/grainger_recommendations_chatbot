import logging
import os
import sys
import boto3
from kubernetes import client, config
from langchain.llms.bedrock import Bedrock
from .utils import bedrock  # Adjust the import path as needed


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
                module_path = "../../.."  # Adjust the relative path as needed
                sys.path.append(os.path.abspath(module_path))

                set_aws_default_region()  # Set AWS_DEFAULT_REGION from Kubernetes secret

                logging.info("Getting bedrock client...")
                boto3_bedrock = bedrock.get_bedrock_client(
                    assumed_role=os.environ.get("BEDROCK_ASSUME_ROLE"),
                    region=os.environ.get("AWS_DEFAULT_REGION"),
                    runtime=False)
                self.bedrock_runtime = bedrock.get_bedrock_client(
                    assumed_role=os.environ.get("BEDROCK_ASSUME_ROLE"),
                    region=os.environ.get("AWS_DEFAULT_REGION"),
                    runtime=False
                )

                logging.info("Initializing Bedrock...")
                model_parameter = {
                    "temperature": 0.0,
                    "top_p": .5,
                    "top_k": 250,
                    "max_tokens_to_sample": 2000,
                    "stop_sequences": ["\n\n Human: bye"]
                }

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


def get_aws_region_from_kubernetes_secret():
    try:
        config.load_kube_config()  # Load Kubernetes config from default location
        v1 = client.CoreV1Api()
        secret_name = 'aws-credentials'
        secret_namespace = 'default'
        secret = v1.read_namespaced_secret(secret_name, secret_namespace)
        aws_region = secret.data.get('AWS_REGION', None)
        if aws_region:
            return aws_region.decode('utf-8')  # Assuming AWS_REGION is base64 encoded
        else:
            return None
    except Exception as e:
        logging.error(f"Error fetching Kubernetes secret: {e}")
        return None


def set_aws_default_region():
    aws_region = get_aws_region_from_kubernetes_secret()
    if aws_region:
        os.environ["AWS_DEFAULT_REGION"] = aws_region
    else:
        os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    llm_initializer = LLMInitializer()
    llm, bedrock_runtime = llm_initializer.check_and_initialize_llm()
