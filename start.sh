#!/bin/bash

cd /app


# Start Streamlit Application
echo "Starting Streamlit Application..."
exec streamlit run modules/main.py --server.port=$PORT --server.address=0.0.0.0 || { echo "Streamlit failed to start"; exit 1; }
