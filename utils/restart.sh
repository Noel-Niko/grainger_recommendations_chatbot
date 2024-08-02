#!/bin/bash

# Load AWS credentials from secrets directory
aws_access_key_id=$(cat /Users/xnxn040/PycharmProjects/grainger_recommendations_chatbot/secrets/aws_access_key_id)
export AWS_ACCESS_KEY_ID=$aws_access_key_id

aws_secret_access_key=$(cat /Users/xnxn040/PycharmProjects/grainger_recommendations_chatbot/secrets/aws_secret_access_key)
export AWS_SECRET_ACCESS_KEY=$aws_secret_access_key

bedrock_assume_role=$(cat /Users/xnxn040/PycharmProjects/grainger_recommendations_chatbot/secrets/bedrock_assume_role)
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

# Running locally
export BACKEND_URL="http://localhost:8000"
echo "BACKEND_URL set to $BACKEND_URL"

# Reload AWS credentials from secrets directory
key_id=$(cat /Users/xnxn040/PycharmProjects/grainger_recommendations_chatbot/secrets/aws_access_key_id)
secret_key=$(cat /Users/xnxn040/PycharmProjects/grainger_recommendations_chatbot/secrets/aws_secret_access_key)
assume_role=$(cat /Users/xnxn040/PycharmProjects/grainger_recommendations_chatbot/secrets/bedrock_assume_role)
export AWS_ACCESS_KEY_ID="$key_id"
export AWS_SECRET_ACCESS_KEY="$secret_key"
export BEDROCK_ASSUME_ROLE="$assume_role"

FASTAPI_PORT=8000
STREAMLIT_PORT=8505

# Start FastAPI on port 8000
echo "Starting FastAPI Application on port $FASTAPI_PORT..."
uvicorn modules.fast_api_main:app --host 0.0.0.0 --port $FASTAPI_PORT &

# Wait a few seconds for FastAPI to start
sleep 5

# Start Streamlit on port 8505
echo "Starting Streamlit UI on port $STREAMLIT_PORT..."
streamlit run /Users/xnxn040/PycharmProjects/grainger_recommendations_chatbot/modules/streamlit_ui.py --server.port $STREAMLIT_PORT --server.address 0.0.0.0 &

echo "FastAPI and Streamlit services have been restarted."

# Keep the script running
wait
