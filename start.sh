#!/bin/bash

# Change to the app directory
cd /app

# Start FastAPI server in the background
echo "Starting FastAPI server..."
uvicorn app:app --host 0.0.0.0 --port 8000 &

# Start Streamlit Application
echo "Starting Streamlit Application..."
exec streamlit run modules/main.py --server.port $PORT --server.address 0.0.0.0 || { echo "Streamlit failed to start"; exit 1; }
