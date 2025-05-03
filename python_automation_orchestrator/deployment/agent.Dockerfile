FROM python:3.10-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=UTC

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY agent_requirements.txt .
RUN pip install --no-cache-dir -r agent_requirements.txt

# Copy agent code
COPY agent/ /app/agent/

# Create required directories
RUN mkdir -p /app/.orchestrator/jobs /app/.orchestrator/packages

# Expose port (optional, for webhooks)
EXPOSE 8080

# Default command
CMD ["python", "-m", "agent.agent_main"]