#!/bin/bash

# Skipper Development Environment Setup Script
# This script sets up the development environment for the Skipper project

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print with timestamp
function log() {
  echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Print success message
function success() {
  log "${GREEN}SUCCESS: $1${NC}"
}

# Print info message
function info() {
  log "${YELLOW}INFO: $1${NC}"
}

# Print error message
function error() {
  log "${RED}ERROR: $1${NC}"
}

# Check if command exists
function command_exists() {
  command -v "$1" &>/dev/null
}

# Check prerequisites
function check_prerequisites() {
  info "Checking prerequisites..."
  
  local missing_prereqs=0
  
  if ! command_exists docker; then
    error "Docker is not installed"
    missing_prereqs=1
  fi
  
  if ! command_exists docker-compose; then
    error "Docker Compose is not installed"
    missing_prereqs=1
  fi
  
  if ! command_exists git; then
    error "Git is not installed"
    missing_prereqs=1
  fi
  
  if ! command_exists python3; then
    error "Python 3 is not installed"
    missing_prereqs=1
  fi
  
  if ! command_exists node; then
    error "Node.js is not installed"
    missing_prereqs=1
  fi
  
  if [ $missing_prereqs -ne 0 ]; then
    error "Please install missing prerequisites and try again"
    exit 1
  fi
  
  success "All prerequisites are installed"
}

# Create directory structure
function create_directories() {
  info "Creating directory structure..."
  
  mkdir -p "${PROJECT_ROOT}/infra/docker/config/prometheus"
  mkdir -p "${PROJECT_ROOT}/infra/docker/config/grafana/provisioning/datasources"
  mkdir -p "${PROJECT_ROOT}/infra/docker/config/grafana/provisioning/dashboards"
  mkdir -p "${PROJECT_ROOT}/infra/docker/config/grafana/dashboards"
  mkdir -p "${PROJECT_ROOT}/infra/docker/config/loki"
  mkdir -p "${PROJECT_ROOT}/infra/docker/config/promtail"
  mkdir -p "${PROJECT_ROOT}/infra/docker/config/redis"
  mkdir -p "${PROJECT_ROOT}/infra/docker/init-scripts/postgres"
  mkdir -p "${PROJECT_ROOT}/infra/docker/init-scripts/rabbitmq"
  
  success "Directory structure created"
}

# Create .env file
function create_env_file() {
  info "Creating .env file..."
  
  if [ ! -f "${PROJECT_ROOT}/.env" ]; then
    cat > "${PROJECT_ROOT}/.env" << EOF
# Skipper Development Environment Variables

# General
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=development_secret_key

# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=skipper
DB_USER=skipper
DB_PASSWORD=development

# Message Broker
BROKER_HOST=rabbitmq
BROKER_PORT=5672
BROKER_USER=guest
BROKER_PASSWORD=guest

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Vault
VAULT_ADDR=http://vault:8200
VAULT_TOKEN=root

# Agents
AGENT_ID=1
LOG_LEVEL=DEBUG
EOF
    
    success ".env file created"
  else
    info ".env file already exists, skipping"
  fi
}

# Configure Git hooks
function configure_git_hooks() {
  info "Configuring Git hooks..."
  
  if [ -d "${PROJECT_ROOT}/.git" ]; then
    # Create pre-commit hook
    cat > "${PROJECT_ROOT}/.git/hooks/pre-commit" << 'EOF'
#!/bin/bash

# Exit on any error
set -e

# Stash any changes not added to the index
git stash -q --keep-index

# Check Python code style with flake8
echo "Running flake8..."
cd backend && python -m flake8
cd ../agents && python -m flake8

# Check Python code formatting with black
echo "Running black..."
cd ../backend && python -m black --check .
cd ../agents && python -m black --check .

# Check JavaScript/TypeScript code style with ESLint
echo "Running ESLint..."
cd ../frontend && npm run lint

# Run backend tests
echo "Running backend tests..."
cd ../backend && python -m pytest -xvs

# Run frontend tests
echo "Running frontend tests..."
cd ../frontend && npm test -- --watchAll=false

# Restore stashed changes
git stash pop -q

echo "Pre-commit checks passed!"
EOF
    
    chmod +x "${PROJECT_ROOT}/.git/hooks/pre-commit"
    
    success "Git hooks configured"
  else
    info "Not a Git repository, skipping Git hooks configuration"
  fi
}

# Set up Python environment
function setup_python_environment() {
  info "Setting up Python environment..."
  
  if [ ! -d "${PROJECT_ROOT}/venv" ]; then
    python3 -m venv "${PROJECT_ROOT}/venv"
    source "${PROJECT_ROOT}/venv/bin/activate"
    
    pip install --upgrade pip
    pip install pre-commit black flake8 pytest pytest-cov
    
    if [ -f "${PROJECT_ROOT}/backend/requirements.txt" ]; then
      pip install -r "${PROJECT_ROOT}/backend/requirements.txt"
    fi
    
    if [ -f "${PROJECT_ROOT}/agents/local/requirements.txt" ]; then
      pip install -r "${PROJECT_ROOT}/agents/local/requirements.txt"
    fi
    
    success "Python environment set up"
  else
    info "Python virtual environment already exists, skipping"
  fi
}

# Set up Node.js environment
function setup_node_environment() {
  info "Setting up Node.js environment..."
  
  if [ -f "${PROJECT_ROOT}/frontend/package.json" ]; then
    cd "${PROJECT_ROOT}/frontend" || exit 1
    npm install
    
    success "Node.js environment set up"
  else
    info "No frontend package.json found, skipping Node.js setup"
  fi
}

# Set up Docker Compose environment
function setup_docker_environment() {
  info "Setting up Docker Compose environment..."
  
  # Copy config files
  cp -f "${SCRIPT_DIR}/docker/config/prometheus/prometheus.yml" "${PROJECT_ROOT}/infra/docker/config/prometheus/"
  cp -f "${SCRIPT_DIR}/docker/config/redis/redis.conf" "${PROJECT_ROOT}/infra/docker/config/redis/"
  cp -f "${SCRIPT_DIR}/docker/init-scripts/postgres/init-db.sh" "${PROJECT_ROOT}/infra/docker/init-scripts/postgres/"
  cp -f "${SCRIPT_DIR}/docker/init-scripts/rabbitmq/rabbitmq.conf" "${PROJECT_ROOT}/infra/docker/init-scripts/rabbitmq/"
  cp -f "${SCRIPT_DIR}/docker/init-scripts/rabbitmq/definitions.json" "${PROJECT_ROOT}/infra/docker/init-scripts/rabbitmq/"
  
  # Create Grafana datasources
  cat > "${PROJECT_ROOT}/infra/docker/config/grafana/provisioning/datasources/datasources.yaml" << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
  
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
EOF
  
  # Create Loki config
  cat > "${PROJECT_ROOT}/infra/docker/config/loki/loki-config.yaml" << EOF
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
    final_sleep: 0s
  chunk_idle_period: 5m
  chunk_retain_period: 30s

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/index
    cache_location: /loki/cache
    cache_ttl: 24h
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s
EOF
  
  # Create Promtail config
  cat > "${PROJECT_ROOT}/infra/docker/config/promtail/promtail-config.yaml" << EOF
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: docker
    static_configs:
      - targets:
          - localhost
        labels:
          job: docker
          __path__: /var/lib/docker/containers/*/*-json.log
    pipeline_stages:
      - json:
          expressions:
            output: log
            stream: stream
            attrs: attrs
      - json:
          expressions:
            tag: tag
          source: attrs
      - regex:
          expression: '(?P<container_name>(?:[^|]*[^|]))\.(?P<container_id>\w+)'
          source: tag
      - timestamp:
          format: RFC3339Nano
          source: time
      - labels:
          container_name:
          container_id:
      - output:
          source: output
EOF
  
  success "Docker Compose environment set up"
}

# Main function
function main() {
  echo "=== Skipper Development Environment Setup ==="
  
  check_prerequisites
  create_directories
  create_env_file
  configure_git_hooks
  setup_python_environment
  setup_node_environment
  setup_docker_environment
  
  echo
  success "Setup completed successfully!"
  echo
  echo "To start the development environment, run:"
  echo "  cd ${PROJECT_ROOT} && docker-compose up -d"
  echo
  echo "To activate the Python virtual environment, run:"
  echo "  source ${PROJECT_ROOT}/venv/bin/activate"
  echo
}

# Run main function
main