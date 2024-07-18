# Use an official Python runtime as a parent image
FROM python:3.11

# Set environment variables for non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies and Firefox-ESR
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    swig \
    firefox-esr \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install GeckoDriver
RUN GECKODRIVER_VERSION=$(curl -sS "https://api.github.com/repos/mozilla/geckodriver/releases/latest" | jq -r ".tag_name") \
    && wget -O /tmp/geckodriver.tar.gz "https://github.com/mozilla/geckodriver/releases/download/$GECKODRIVER_VERSION/geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz" \
    && tar -xzf /tmp/geckodriver.tar.gz -C /usr/local/bin/ \
    && rm /tmp/geckodriver.tar.gz

# Set display port to avoid crash
ENV DISPLAY=:99

# Set working directory
WORKDIR /app

# Copy application code to the container
COPY . /app

# Set PYTHONPATH
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt --verbose

# Clean up to reduce image size
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Expose necessary ports
EXPOSE 8000
EXPOSE 8505

# Health checks for FastAPI and Streamlit
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD curl -f http://localhost:8000/health || exit 1
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD curl -f http://localhost:8505/health || exit 1

# Make the start script executable
RUN chmod +x /app/start.sh

# Run the start.sh script
CMD ["./start.sh"]
