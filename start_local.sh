#!/bin/bash
AWS_REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"
export AWS_REGION

# Define the range of ports to try
port_range=(8000 8001 8500 8505 9000)

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