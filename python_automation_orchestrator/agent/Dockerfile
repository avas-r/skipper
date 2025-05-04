FROM python:3.11-slim

WORKDIR /app

# Copy requirements first to leverage Docker layer caching
COPY agent_requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r agent_requirements.txt

# Copy agent code
COPY agent/ agent/
COPY run_agent.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV AGENT_HEADLESS=1

# Run the agent in headless mode
ENTRYPOINT ["python", "run_agent.py", "--headless"]
CMD ["--server", "https://your-orchestrator-server", "--tenant", "your-tenant-id"]