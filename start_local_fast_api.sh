#!/bin/bash

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
