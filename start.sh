#!/bin/bash

cd /app

aws_access_key_id=$(cat aws_access_key_id)
export AWS_ACCESS_KEY_ID=$aws_access_key_id

aws_secret_access_key=$(cat aws_secret_access_key)
export AWS_SECRET_ACCESS_KEY=$aws_secret_access_key

bedrock_assume_role=$(cat bedrock_assume_role)
export BEDROCK_ASSUME_ROLE=$bedrock_assume_role

AWS_REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"
export AWS_REGION

FASTAPI_PORT=8000

# Start FastAPI
echo "Starting FastAPI Application on port $FASTAPI_PORT..."
uvicorn modules.fast_api_main:app --host 0.0.0.0 --port $FASTAPI_PORT &

# Wait a few seconds for FastAPI to start
sleep 5

STREAMLIT_PORT=8505
# Start Streamlit UI on port 8505
echo "Starting Streamlit UI on port $STREAMLIT_PORT..."
streamlit run streamlit_ui.py --server.port $STREAMLIT_PORT &

echo "Both FastAPI and Streamlit are running."

# Keep the script running
wait
