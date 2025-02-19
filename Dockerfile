# Use an official Python runtime as a parent image
FROM python:3.9.18-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required by CairoSVG, Graphviz, and for compiling Python packages
RUN apt-get update && apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    graphviz \
    pkg-config \
    libcairo2-dev \
    gcc \ 
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=server.py

# Run server.py when the container launches
CMD ["flask", "run", "--host=0.0.0.0"]
