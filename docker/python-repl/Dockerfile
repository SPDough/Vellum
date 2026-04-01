# Python REPL Docker Container for LangChain Workflows
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Create non-root user for security
RUN groupadd -r repluser && useradd -r -g repluser repluser

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for execution
RUN mkdir -p /app/executions /app/logs && \
    chown -R repluser:repluser /app

# Set resource limits (will be enforced by Docker run)
# Memory: 512MB, CPU: 0.5 cores, Execution time: 30s max

# Switch to non-root user
USER repluser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the REPL service
CMD ["python", "main.py"]