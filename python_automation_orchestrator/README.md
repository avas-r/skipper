# Python Automation Orchestrator

An enterprise-grade system for managing Python automation scripts at scale.

## Overview

Python Automation Orchestrator is a comprehensive platform for managing, scheduling, and monitoring Python-based automation scripts across an organization. Similar to UiPath Orchestrator but specifically designed for Python, this system provides a scalable, secure, and feature-rich environment for automation at enterprise scale.

### Key Features

- **Asset Management**: Secure storage and management of credentials and configurations
- **Queue Management**: Prioritized work item processing with transaction handling
- **Scheduling**: Flexible job scheduling with cron expressions and dependencies
- **Role-Based Access Control**: Granular permissions for all system resources
- **Multi-tenancy**: Complete isolation between tenants with resource quotas
- **Agent Management**: Monitoring and management of distributed automation agents
- **Job Execution Tracking**: Detailed logging and execution history
- **Notification System**: Configurable alerts for job status and system events

## Architecture

The system is built with a modern, microservices-inspired architecture:

- **API Layer**: FastAPI-based REST endpoints with OpenAPI documentation
- **Service Layer**: Modular services with specific responsibilities
- **Messaging Layer**: Asynchronous communication using RabbitMQ
- **Data Layer**: PostgreSQL for transactional data and MinIO for object storage
- **Agent Layer**: Lightweight Python agents running on client machines

## Technical Stack

- **Backend**: Python 3.9+ with FastAPI and SQLAlchemy
- **Database**: PostgreSQL 13+
- **Message Broker**: RabbitMQ
- **Object Storage**: MinIO (S3-compatible)
- **Frontend**: (Planned) React-based web interface
- **Containerization**: Docker with Kubernetes orchestration support

## Getting Started

### Prerequisites

- Python 3.9 or higher
- PostgreSQL 13 or higher
- RabbitMQ 3.8 or higher
- MinIO or S3-compatible object storage

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/python-automation-orchestrator.git
   cd python-automation-orchestrator
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Initialize the database:
   ```bash
   alembic upgrade head
   ```

5. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Agent Installation

#### Method 1: Direct Installation

1. Install agent dependencies:
   ```bash
   pip install -r agent_requirements.txt
   ```

2. Run the agent with the helper script:
   ```bash
   # Configure and run the agent
   python run_agent.py --server https://your-orchestrator-server --tenant your-tenant-id
   
   # Use headless mode for machines without GUI
   python run_agent.py --server https://your-orchestrator-server --tenant your-tenant-id --headless
   ```

#### Method 2: Docker Container

Use the provided Docker helper script to build and run the agent in a container:

```bash
# Build and run agent with Docker
./run_agent_docker.sh --server https://your-orchestrator-server --tenant your-tenant-id
```

You can also build the Docker image manually:

```bash
# Build the Docker image
docker build -t automation-agent -f agent/Dockerfile .

# Run the container
docker run --rm automation-agent --server https://your-orchestrator-server --tenant your-tenant-id
```

#### Agent Configuration

The agent can be configured with the following command-line arguments:

- `--server`: URL of the orchestrator server
- `--tenant`: ID of your tenant
- `--headless`: Run in headless mode (no GUI components)

Additional configuration is stored in `~/.orchestrator/agent_config.json` and includes:

- API credentials
- Agent capabilities
- Heartbeat intervals
- Package directories
- Logging settings

## Documentation

API documentation is available at `/docs` when the server is running.

For full documentation, see the `docs/` directory.

## Examples

We provide several examples to help you get started:

- **Local Testing**: See `examples/local_testing.md` for instructions on testing with a local server setup
- **Mock Server**: Use `examples/mock_server.py` to quickly test agent functionality without a full orchestrator deployment
- **Agent Configuration**: Review the agent section above for details on running the agent component

## Development

### Running Tests

```bash
pytest
```

### Database Migrations

```bash
# Create a migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head
```

## Deployment

### Docker

```bash
# Build containers
docker-compose build

# Start services
docker-compose up -d
```

### Kubernetes

Kubernetes manifests are provided in the `deployment/kubernetes/` directory.

```bash
kubectl apply -f deployment/kubernetes/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- FastAPI and Pydantic for the excellent API framework
- SQLAlchemy for ORM capabilities
- Alembic for database migrations
- RabbitMQ for messaging
- MinIO for object storage