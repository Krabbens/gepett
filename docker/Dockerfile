# Base image with PyTorch, CUDA 12.1, and cuDNN 8
FROM pytorch/pytorch:2.3.0-cuda12.1-cudnn8-devel

# Set the working directory
WORKDIR /app

# Install system dependencies
# git is needed for some pip installs, procps for process management (ps)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and project configuration first to leverage Docker caching
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
# Using --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY gepett/ ./gepett
COPY skills/ ./skills

# Install the project itself in editable mode
# This makes the `gepett` package available for import
RUN pip install -e .

# Set a default command to run when the container starts.
# This will be overridden by docker-compose.yml for specific tasks.
CMD ["/bin/bash"]
