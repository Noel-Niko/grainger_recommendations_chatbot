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

# Define the range of ports to try
port_range=(8000 8001 8500 8505 9000 9001 9002 9003 9004 9004 9006 9007 9008 9009)

for port in "${port_range[@]}"; do
    # Use Python to check if the port is available
    python -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.bind(('localhost', $port)); s.close(); print('Port $port is available')" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        # Port is available, start Streamlit with this port
        echo "Starting Streamlit Application..."
        exec  streamlit run modules/main.py --server.port=$port --server.address=0.0.0.0 || { echo "Streamlit failed to start"; exit 1; }
        break
    fi
done

if [ $? -ne 0 ]; then
    echo "No available port found in the specified range."
    echo "Initialization failed. Exiting."
    exit 1
fi