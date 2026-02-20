FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy all source code
COPY . .

# Expose port 7860 (Hugging Face default)
EXPOSE 7860

# Start the server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860"]
