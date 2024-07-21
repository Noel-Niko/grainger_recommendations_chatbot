FROM python:3.11-slim

# Set environment variables for non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Enable shell debugging mode
RUN set -x \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        wget \
        unzip \
        curl \
        gnupg \
        jq \
        xdg-utils \
        libglib2.0-0 \
        libnss3 \
        libgconf-2-4 \
        libfontconfig1 \
        libx11-xcb1 \
        libxcomposite1 \
        libxdamage1 \
        libxi6 \
        libxtst6 \
        libxrandr2 \
        libasound2 \
        libpangocairo-1.0-0 \
        libatk1.0-0 \
        libgtk-3-0 \
        libgbm-dev \
        ca-certificates \
        build-essential \
        libhdf5-dev \
        python3-dev \
        g++ \
        zlib1g-dev \
        libjpeg-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome and ChromeDriver
RUN echo "Checking network connectivity..." \
    && curl -I --insecure https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json \
    && echo "Fetching the latest stable Chrome and ChromeDriver versions..." \
    && curl -s --insecure https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json -o /tmp/chrome_versions.json \
    && echo "Contents of /tmp/chrome_versions.json:" \
    && cat /tmp/chrome_versions.json \
    && VERSION=$(jq -r '.channels.Stable.version' /tmp/chrome_versions.json) \
    && if [ -z "$VERSION" ]; then echo "Failed to fetch Chrome version"; exit 1; fi \
    && echo "Latest stable version: $VERSION" \
    && CHROME_URL=$(jq -r --arg VERSION "$VERSION" '.channels.Stable.downloads.chrome[] | select(.platform=="linux64") | .url' /tmp/chrome_versions.json) \
    && echo "Chrome URL: ${CHROME_URL}" \
    && CHROMEDRIVER_URL=$(jq -r --arg VERSION "$VERSION" '.channels.Stable.downloads.chromedriver[] | select(.platform=="linux64") | .url' /tmp/chrome_versions.json) \
    && if [ -z "$CHROME_URL" ] || [ -z "$CHROMEDRIVER_URL" ]; then echo "Failed to fetch Chrome or ChromeDriver URL"; exit 1; fi \
    && echo "Chrome URL: ${CHROME_URL}" \
    && echo "Chrome Driver URL: ${CHROMEDRIVER_URL}" \
    && echo "Downloading Chrome from $CHROME_URL" \
    && curl -o /tmp/chrome-linux.zip -L $CHROME_URL \
    && unzip -o /tmp/chrome-linux.zip -d /opt \
    && rm /tmp/chrome-linux.zip \
    && ln -s /opt/chrome-linux64/chrome-linux/chrome /usr/local/bin/google-chrome \
    && echo "Downloading ChromeDriver from $CHROMEDRIVER_URL" \
    && curl -o /tmp/chromedriver-linux.zip -L $CHROMEDRIVER_URL \
    && unzip -o /tmp/chromedriver-linux.zip -d /usr/local/bin/ \
    && mv /usr/local/bin/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && rm -rf /tmp/chromedriver-linux.zip \
    && chmod +x /usr/local/bin/chromedriver \
    && echo "Chrome and ChromeDriver installed successfully."

# Set display port to avoid crash
ENV DISPLAY=:99

# Set environment variables
ENV CHROME_BIN=/usr/local/bin/google-chrome
ENV CHROME_DRIVER=/usr/local/bin/chromedriver
ENV PATH=$PATH:/usr/local/bin
ENV PYTHONPATH="/app"
ENV HDF5_DIR=/usr/lib/x86_64-linux-gnu/hdf5/serial/

# Set working directory
WORKDIR /app

# Copy application code to the container
COPY . /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt --verbose

# Clean up to reduce image size
RUN apt-get remove -y wget unzip curl gnupg jq xdg-utils build-essential \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Expose necessary ports
EXPOSE 8000
EXPOSE 8505

# Health checks for FastAPI
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD curl -f http://localhost:8000/health || exit 1

# Make the start script executable
RUN chmod +x /app/start.sh

# Run the start.sh script
CMD ["./start.sh"]
