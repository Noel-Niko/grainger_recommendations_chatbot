import logging
import os
from typing import Optional

import boto3
from botocore.config import Config

tag = "get_bedrock_client"

def get_bedrock_client(
    assumed_role: Optional[str] = None,
    region: Optional[str] = None,
    runtime: Optional[bool] = True
):
    """Create a boto3 client for Amazon Bedrock, with optional configuration overrides

    Parameters
    ----------
    assumed_role :
        Optional ARN of an AWS IAM role to assume for calling the Bedrock service. If not
        specified, the current active credentials will be used.
    region :
        Optional name of the AWS Region in which the service should be called (e.g. "us-east-1").
        If not specified, AWS_REGION or AWS_DEFAULT_REGION environment variable will be used.
    runtime :
        Optional choice of getting different client to perform operations with the Amazon Bedrock service.
    """
    # Access the environment variables
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    bedrock_assume_role = os.getenv('BEDROCK_ASSUME_ROLE')
    allow_insecure = os.getenv('ALLOW_INSECURE_CONNECTIONS', 'false').lower() == 'true'

    logging.info(f"{tag} /  AWS_REGION: {os.getenv('AWS_REGION')}")
    target_region = os.environ.get("AWS_REGION", "us-east-1") if region is None else region

    logging.info(f"{tag} / Create new client\n  Using region: {target_region}")
    session_kwargs = {"region_name": target_region}
    client_kwargs = {**session_kwargs}

    profile_name = os.environ.get("AWS_PROFILE")
    if profile_name:
        logging.info(f"{tag} / Using profile: {profile_name}")
        session_kwargs["profile_name"] = profile_name

    retry_config = Config(
        region_name=target_region,
        retries={
            "max_attempts": 10,
            "mode": "standard",
        },
    )
    session = boto3.Session(**session_kwargs)

    if assumed_role or bedrock_assume_role:
        role_to_assume = assumed_role if assumed_role else bedrock_assume_role
        logging.info(f"{tag} / Using role: {role_to_assume}")
        sts = session.client("sts")
        response = sts.assume_role(
            RoleArn=str(role_to_assume),
            RoleSessionName="langchain-llm-1"
        )
        logging.info(" ... successful!")
        client_kwargs["aws_access_key_id"] = response["Credentials"]["AccessKeyId"]
        client_kwargs["aws_secret_access_key"] = response["Credentials"]["SecretAccessKey"]
        client_kwargs["aws_session_token"] = response["Credentials"]["SessionToken"]
    else:
        client_kwargs["aws_access_key_id"] = aws_access_key_id
        client_kwargs["aws_secret_access_key"] = aws_secret_access_key

    service_name = "bedrock-runtime" if runtime else "bedrock"

    bedrock_client = session.client(
        service_name=service_name,
        config=retry_config,
        verify=not allow_insecure,
        **client_kwargs
    )

    logging.info("boto3 Bedrock client successfully created!")
    logging.info(bedrock_client._endpoint)
    return bedrock_client
