#!/bin/bash

aws_access_key_id=$(cat aws_access_key_id)
export AWS_ACCESS_KEY_ID=$aws_access_key_id

aws_secret_access_key=$(cat aws_secret_access_key)
export AWS_SECRET_ACCESS_KEY=$aws_secret_access_key

bedrock_assume_role=$(cat bedrock_assume_role)
export BEDROCK_ASSUME_ROLE=$bedrock_assume_role

AWS_REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"
export AWS_REGION

# Define the ports to be freed
PORTS=(8000 8505)

# Function to kill processes using specified ports
kill_processes_on_ports() {
  for PORT in "${PORTS[@]}"; do
    # Find the process IDs using the port
    PIDS=$(lsof -t -i:$PORT)

    if [ -z "$PIDS" ]; then
      echo "No process found on port $PORT"
    else
      echo "Killing processes on port $PORT: $PIDS"
      # Kill the processes
      kill -9 $PIDS
    fi
  done
}

# Execute the function
kill_processes_on_ports

echo "Ports are now free."

# Ensure the FIREFOX_BINARY_PATH is set correctly
export FIREFOX_BINARY_PATH=$(which firefox)
if [ -z "$FIREFOX_BINARY_PATH" ]; then
    echo "Firefox binary not found. Please install Firefox or set the FIREFOX_BINARY_PATH environment variable."
    exit 1
fi

FASTAPI_PORT=8000
STREAMLIT_PORT=8505

# Start FastAPI on port 8000
echo "Starting FastAPI Application on port $FASTAPI_PORT..."
uvicorn modules.fast_api_main:app --host 0.0.0.0 --port $FASTAPI_PORT &

# Wait a few seconds for FastAPI to start
sleep 5

# Start Streamlit on port 8505
echo "Starting Streamlit UI on port $STREAMLIT_PORT..."
streamlit run streamlit_ui.py --server.port $STREAMLIT_PORT --server.address 0.0.0.0 &

echo "FastAPI and Streamlit services have been restarted."

# Keep the script running
wait
