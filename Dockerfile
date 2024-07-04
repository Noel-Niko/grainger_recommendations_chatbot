
FROM python:3.12
# Set environment variables for non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y wget && apt-get clean

COPY . /app

WORKDIR /app

ENV PYTHONPATH="/app:${PYTHONPATH}"

# Install system level dependencies not available via pip
RUN apt-get update && apt-get install -y swig

# Install pip required install(s)
RUN pip install -r requirements.txt

# Clean up to reduce image size
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

EXPOSE 8505

# Make the script executable
RUN chmod +x /app/start.sh

ENTRYPOINT ["./start.sh"]