import logging

bedrock_runtime = None
llm = None


def check_and_initialize_llm():
    global bedrock_runtime
    global llm
    try:
        logging.info("Checking if 'llm' is defined...")
        if llm is None:
            import json
            import os
            import sys
            import boto3
            import botocore

            from langchain.llms.bedrock import Bedrock
            from IPython.display import Image

            module_path = "../.."
            sys.path.append(os.path.abspath(module_path))
            from utils import bedrock, print_ww

            os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

            logging.info("Getting bedrock client...")
            boto3_bedrock = bedrock.get_bedrock_client(
                assumed_role=os.environ.get("BEDROCK_ASSUME_ROLE", None),
                region=os.environ.get("AWS_DEFAULT_REGION", None),
                runtime=False)

            bedrock_runtime = bedrock.get_bedrock_client(
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
            llm = Bedrock(
                model_id="anthropic.claude-v2",
                model_kwargs=model_parameter,
                client=bedrock_runtime
            )
        logging.info("'llm' initialized successfully.")
        return llm
    except Exception as e:
        logging.error(f"Error initializing LLM: {str(e)}")
        raise e  # re-raise the exception to stop the execution

# def check_and_initialize_llm():
#     global bedrock_runtime
#     global llm
#     try:
#         # Check if 'llm' is defined
#         if 'llm' not in globals():
#             import json
#             import os
#             import sys
#             import boto3
#             import botocore
#
#             from langchain.llms.bedrock import Bedrock
#             from IPython.display import Image
#
#             module_path = "../.."
#             sys.path.append(os.path.abspath(module_path))
#             from utils import bedrock, print_ww
#
#             os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
#
#             boto3_bedrock = bedrock.get_bedrock_client(
#                 assumed_role=os.environ.get("BEDROCK_ASSUME_ROLE", None),
#                 region=os.environ.get("AWS_DEFAULT_REGION", None),
#                 runtime=False)
#
#             bedrock_runtime = bedrock.get_bedrock_client(
#                 assumed_role=os.environ.get("BEDROCK_ASSUME_ROLE", None),
#                 region=os.environ.get("AWS_DEFAULT_REGION", None))
#
#             model_parameter = {
#                 "temperature": 0.0,
#                 "top_p": .5,
#                 "top_k": 250,
#                 "max_tokens_to_sample": 2000,
#                 "stop_sequences": ["\n\n Human: bye"]
#             }
#
#             llm = Bedrock(
#                 model_id="anthropic.claude-v2",
#                 model_kwargs=model_parameter,
#                 client=bedrock_runtime
#             )
#         return llm
#     except Exception as e:
#         print(f"Error initializing LLM: {str(e)}")
#         raise e  # re-raise the exception to stop the execution

# def check_and_initialize_llm():
#     global bedrock_runtime
#     global llm
#     try:
#         # Check if 'llm' is defined
#         if 'llm' not in globals():
#             import json
#             import os
#             import sys
#             import boto3
#             import botocore
#
#             from langchain.llms.bedrock import Bedrock
#             from IPython.display import Image
#
#             module_path = ".."
#             sys.path.append(os.path.abspath(module_path))
#             from utils import bedrock, print_ww
#
#             os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
#
#             boto3_bedrock = bedrock.get_bedrock_client(
#                 assumed_role=os.environ.get("BEDROCK_ASSUME_ROLE", None),
#                 region=os.environ.get("AWS_DEFAULT_REGION", None),
#                 runtime=False)
#
#             bedrock_runtime = bedrock.get_bedrock_client(
#                 assumed_role=os.environ.get("BEDROCK_ASSUME_ROLE", None),
#                 region=os.environ.get("AWS_DEFAULT_REGION", None))
#
#             model_parameter = {
#                 "temperature": 0.0,
#                 "top_p": .5,
#                 "top_k": 250,
#                 "max_tokens_to_sample": 2000,
#                 "stop_sequences": ["\n\n Human: bye"]
#             }
#
#             llm = Bedrock(
#                 model_id="anthropic.claude-v2",
#                 model_kwargs=model_parameter,
#                 client=bedrock_runtime
#             )
#     except Exception as e:
#         print(f"Error initializing LLM: {str(e)}")
