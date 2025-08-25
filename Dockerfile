# Use Python 3.13 slim image as base
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from pyproject.toml and install with pip
COPY pyproject.toml ./

# Extract dependencies and install with pip
RUN pip install fastapi==0.116.0 httpx==0.28.1 "psycopg[binary,pool]==3.2.9" \
    pydantic==2.11.7 "passlib[bcrypt]==1.7.4" pytest==8.4.1 uvicorn==0.35.0 \
    python-multipart==0.0.20 pytest-xdist==3.8.0 "pyjwt>=2.10.1" ruff==0.6.5 \
    "boto3>=1.39.9" "pydantic-settings>=2.10.1" "isort>=6.0.1"

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8000

# Set Python path
ENV PYTHONPATH=/app

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]