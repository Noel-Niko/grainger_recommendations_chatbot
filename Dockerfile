
FROM python:3.11
# Set environment variables for non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y wget && apt-get clean

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable

# Install ChromeDriver
RUN CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE) && \
    wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip && \
    unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

# Set display port to avoid crash
ENV DISPLAY=:99

COPY . /app

WORKDIR /app

ENV PYTHONPATH="/app:${PYTHONPATH}"

# Install system level dependencies not available via pip
RUN apt-get update && apt-get install -y swig

# Install pip required install(s)
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt --verbose

# Clean up to reduce image size
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

EXPOSE 8000
EXPOSE 8505

# Make the script executable
RUN chmod +x /app/start.sh

ENTRYPOINT ["./start.sh"]