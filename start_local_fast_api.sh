#!/bin/bash

aws_access_key_id=$(cat aws_access_key_id)
export AWS_ACCESS_KEY_ID=$aws_access_key_id

aws_secret_access_key=$(cat aws_secret_access_key)
export AWS_SECRET_ACCESS_KEY=$aws_secret_access_key

bedrock_assume_role=$(cat bedrock_assume_role)
export BEDROCK_ASSUME_ROLE=$bedrock_assume_role

AWS_REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"
export AWS_REGION

# Define the port for FastAPI
FASTAPI_PORT=8000

# Start FastAPI
echo "Starting FastAPI Application on port $FASTAPI_PORT..."
nohup uvicorn modules.fast_api_main:app --host 0.0.0.0 --port $FASTAPI_PORT > >(tee -a nohup.out) 2>&1 &

# Wait a few seconds for FastAPI to start
sleep 3

# Start Streamlit UI on port 8505
echo "Starting Streamlit UI on port 8505..."
nohup streamlit run streamlit_ui.py --server.port 8505 > >(tee -a nohup.out) 2>&1 &

echo "Both FastAPI and Streamlit are running."
