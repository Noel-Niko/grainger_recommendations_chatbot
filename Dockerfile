# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables for non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    jq \
    swig \
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
    && rm -rf /var/lib/apt/lists/*

# Install Chrome and ChromeDriver
RUN echo "Downloading and installing Google Chrome..." \
    && CHROME_URL=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json | jq -r '.channels.Stable.downloads.chrome[] | select(.platform=="linux64") | .url') \
    && curl -o /tmp/chrome-linux.zip -L $CHROME_URL \
    && unzip -o /tmp/chrome-linux.zip -d /opt \
    && rm /tmp/chrome-linux.zip \
    && ln -s /opt/chrome-linux64/chrome-linux/chrome /usr/local/bin/google-chrome \
    && echo "Google Chrome installed successfully." \
    && echo "Downloading and installing ChromeDriver..." \
    && CHROMEDRIVER_URL=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json | jq -r '.channels.Stable.downloads.chromedriver[] | select(.platform=="linux64") | .url') \
    && curl -o /tmp/chromedriver-linux.zip -L $CHROMEDRIVER_URL \
    && unzip -o /tmp/chromedriver-linux.zip -d /usr/local/bin/ \
    && rm -rf /tmp/chromedriver-linux.zip \
    && chmod +x /usr/local/bin/chromedriver \
    && echo "ChromeDriver installed successfully."

# Set display port to avoid crash
ENV DISPLAY=:99

COPY . /app

# Set environment variables for Chrome and ChromeDriver
ENV RUNNING_IN_DOCKER=true
ENV CHROME_BIN=/usr/local/bin/google-chrome
ENV CHROME_DRIVER=/usr/local/bin/chromedriver

# Add Chrome and ChromeDriver to PATH
ENV PATH=$PATH:/usr/local/bin

# Set PYTHONPATH
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Set working directory
WORKDIR /app

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
