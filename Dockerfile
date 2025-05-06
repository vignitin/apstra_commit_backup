FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for SSH/SCP
RUN apt-get update && apt-get install -y \
    openssh-client \
    sshpass \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for data and logs
RUN mkdir -p data logs

# Run the application
CMD ["python", "app/main.py"]
