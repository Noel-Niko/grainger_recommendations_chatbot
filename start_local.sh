#!/bin/bash

# Print Python version
echo "*********************************************************Python version:"
python --version

# Print faiss-cpu version
echo "*********************************************************faiss-cpu version:"
python -c 'import faiss; print(faiss.__version__)'

#
##TODO: *****ADJUST FOR YOUR DEVICE***** for running locally only:
## Set the project root directory as PYTHONPATH
#export PYTHONPATH="/Users/noel_niko/PycharmProjects/grainger_rag:$PYTHONPATH"
#
## Run the Preprocessing file
#echo "********************************************************* Preprocessing Data...:"
#python rag_application/modules/preprocess_data.py || { echo "Preprocessing failed"; exit 1; }
#
## Remove the existing pickle file if it exists
#echo "********************************************************* Removing existing pickle file (if any)..."
#rm -f vector_index.pkl

# Define the range of ports to try
port_range=(8000 8001 8500 8505 9000)

for port in "${port_range[@]}"; do
    # Use Python to check if the port is available
    python -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.bind(('localhost', $port)); s.close(); print('Port $port is available')" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        # Port is available, start Streamlit with this port
        echo "Starting Streamlit Application..."
        exec  streamlit run /Users/noel_niko/PycharmProjects/graigner_recommendations_chatbot/modules/user_interface.py --server.port=$port --server.address=0.0.0.0 || { echo "Streamlit failed to start"; exit 1; }
        break
    fi
done

if [ $? -ne 0 ]; then
    echo "No available port found in the specified range."
    echo "Initialization failed. Exiting."
    exit 1
fi