#!/bin/bash

# Ensure the script is executed from the correct directory
cd /app

# Start the application
echo "Starting the application..."
# Replace this with the actual command(s) to start your application
# For example, if you're using FastAPI with uvicorn and Streamlit:
# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Start Streamlit server (if applicable)
streamlit run app/streamlit_app.py --server.port 8505

# Wait for background processes to finish
wait
