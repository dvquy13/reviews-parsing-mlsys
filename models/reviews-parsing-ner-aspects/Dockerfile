# Use a slim version of the official Python image as a base image
FROM python:3.9.19-slim

# Set the working directory in the container
WORKDIR /app

# Copy the necessary files into the container
COPY model-settings.json model.py requirements.no-gpu.txt settings.json /app/

# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    pip install torch==2.3.1+cpu torchvision==0.18.1+cpu --index-url https://download.pytorch.org/whl/cpu && \
    pip install -r requirements.no-gpu.txt && \
    apt-get remove -y build-essential && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Set the entrypoint
ENTRYPOINT ["mlserver", "start", "."]
