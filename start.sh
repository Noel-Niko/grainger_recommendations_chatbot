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

# Set the backend URL based on the environment
export BACKEND_URL="http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000"

# Set the Firefox binary path
if [ -z "$FIREFOX_BINARY_PATH" ]; then
    if [ -x "$(command -v firefox)" ]; then
        export FIREFOX_BINARY_PATH=$(command -v firefox)
    elif [ -x "/usr/bin/firefox" ]; then
        export FIREFOX_BINARY_PATH="/usr/bin/firefox"
    else
        echo "Firefox binary not found. Please install Firefox or set the FIREFOX_BINARY_PATH environment variable."
        exit 1
    fi
fi

FASTAPI_PORT=8000

# Start FastAPI
echo "Starting FastAPI Application on port $FASTAPI_PORT..."
uvicorn modules.fast_api_main:app --host 0.0.0.0 --port $FASTAPI_PORT &

# Wait a few seconds for FastAPI to start
sleep 5

STREAMLIT_PORT=8505

echo "Starting Streamlit UI on port $STREAMLIT_PORT..."
streamlit run streamlit_ui.py --server.port $STREAMLIT_PORT --server.address 0.0.0.0 &

echo "Both FastAPI and Streamlit are running."

# Keep the script running
wait
