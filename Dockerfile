FROM python:3.11-slim

WORKDIR /app

# Install awscli v2
RUN apt-get update && apt-get install -y curl unzip \
 && curl https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip -o awscliv2.zip \
 && unzip awscliv2.zip \
 && ./aws/install \
 && rm -rf awscliv2.zip aws


# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Create data directories
RUN mkdir -p data/raw data/processed

# Default command
CMD ["python", "-m", "scripts.run_etl", "--help"]
