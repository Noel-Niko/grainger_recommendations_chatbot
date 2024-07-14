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

# Execute the function
kill_processes_on_ports

echo "Ports are now free."

# Start FastAPI on port 8000
 nohup uvicorn modules.fast_api_main:app --host 0.0.0.0 --port 8000 > >(tee -a nohup.out) 2>&1 &

# Wait a few seconds for FastAPI to start
sleep 5

# Start Streamlit on port 8505
 nohup streamlit run streamlit_ui.py --server.port 8505 > >(tee -a nohup.out) 2>&1 &

 echo "FastAPI and Streamlit services have been restarted."
