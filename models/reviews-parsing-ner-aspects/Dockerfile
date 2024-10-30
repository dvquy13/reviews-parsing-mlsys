# Use a slim version of the official Python image as a base image
FROM python:3.9.19-slim

# Set the working directory in the container
WORKDIR /app

# Install Torch first because it's required but slowed to install
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    pip install torch==2.3.1+cpu --index-url https://download.pytorch.org/whl/cpu && \
    apt-get remove -y build-essential && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Copy only the requirements file first to leverage Docker layer caching
COPY requirements.no-gpu.txt /app/

RUN pip install -r requirements.no-gpu.txt && \
    apt-get remove -y build-essential && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Remove as no need after installation
RUN rm -f requirements.no-gpu.txt

# Copy the rest of the application files
COPY model-settings.json model.py settings.json /app/

EXPOSE 8080

# Set the entrypoint
ENTRYPOINT ["mlserver", "start", "."]
