#!/bin/bash

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

# Start FastAPI on port 8000
 nohup uvicorn modules.fast_api_main:app --host 0.0.0.0 --port 8000 > >(tee -a nohup.out) 2>&1 &

# Wait a few seconds for FastAPI to start
sleep 3

# Start Streamlit on port 8505
 nohup streamlit run streamlit_ui.py --server.port 8505 > >(tee -a nohup.out) 2>&1 &

 echo "FastAPI and Streamlit services have been restarted."
