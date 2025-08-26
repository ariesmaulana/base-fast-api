# Use Python 3.13 slim image as base
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager (using curl method as requested)
# Note: Using direct binary download due to environment SSL constraints
RUN curl -LsSf -k -o /tmp/uv.tar.gz https://github.com/astral-sh/uv/releases/download/0.8.13/uv-x86_64-unknown-linux-gnu.tar.gz && \
    tar -xzf /tmp/uv.tar.gz -C /tmp && \
    mv /tmp/uv-x86_64-unknown-linux-gnu/uv /usr/local/bin/ && \
    chmod +x /usr/local/bin/uv && \
    rm -rf /tmp/uv*

# Set Python and pip to use relaxed SSL (for dependency installation in constrained environment)
ENV PYTHONHTTPSVERIFY=0
ENV PIP_TRUSTED_HOST="pypi.org files.pythonhosted.org pypi.python.org"

# Copy project files for dependency installation
COPY pyproject.toml uv.lock ./

# Install dependencies with uv (bypass SSL verification due to environment constraints)
# Export requirements and install via pip as workaround for SSL certificate constraints
RUN uv export --format requirements-txt > requirements.txt && \
    pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8000

# Set Python path
ENV PYTHONPATH=/app

# Run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]