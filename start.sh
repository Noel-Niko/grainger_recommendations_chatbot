#!/bin/bash

cd /app || exit

FASTAPI_PORT=8000
STREAMLIT_PORT=8505

# Declare variables to hold the contents of the secret files
key_id=$(cat /app/secrets/aws_access_key_id)
secret_key=$(cat /app/secrets/aws_secret_access_key)
assume_role=$(cat /app/secrets/bedrock_assume_role)

# Export the variables as environment variables
export AWS_ACCESS_KEY_ID="$key_id"
export AWS_SECRET_ACCESS_KEY="$secret_key"
export BEDROCK_ASSUME_ROLE="$assume_role"

# Set Streamlit to run in headless mode and skip the email prompt
export STREAMLIT_BROWSER_GATHERUSAGESTATS=false
export STREAMLIT_SERVER_HEADLESS=true

# Update CA certificates
update-ca-certificates
export ALLOW_INSECURE_CONNECTIONS=true

# Start the application
echo "Starting the application..."
# Start the Redis server
REDIS_CONF_PATH="/app/redis.conf"
if [ -f "$REDIS_CONF_PATH" ]; then
    echo "Starting Redis server with config $REDIS_CONF_PATH..."
    redis-server "$REDIS_CONF_PATH" &
else
    echo "Redis configuration file not found at $REDIS_CONF_PATH"
    exit 1
fi

# Wait a few seconds for Redis to start
sleep 5

# Check if Redis is running
if lsof -i:6379; then
  echo "Redis is running on port 6379."
else
  echo "Redis did not start successfully."
  exit 1
fi

# Start FastAPI on port 8000
echo "Starting FastAPI Application on port $FASTAPI_PORT..."
gunicorn modules.fast_api_main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$FASTAPI_PORT --access-logfile - --timeout 60 &

# Wait a few seconds for FastAPI to start
sleep 5

# Start Streamlit on port 8505
echo "Starting Streamlit UI on port $STREAMLIT_PORT..."
streamlit run /app/modules/streamlit_ui.py --server.port $STREAMLIT_PORT --server.address 0.0.0.0 > /app/streamlit.log 2>&1 &

echo "FastAPI and Streamlit services have been started."

# Keep the script running
wait
