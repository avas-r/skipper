#!/bin/bash

# Run Agent in Docker
# This script builds and runs the agent in a Docker container

# Default values
SERVER_URL="https://your-orchestrator-server"
TENANT_ID="your-tenant-id"
IMAGE_NAME="automation-agent"

# Show help
show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -s, --server URL    Set orchestrator server URL (required)"
    echo "  -t, --tenant ID     Set tenant ID (required)"
    echo "  -i, --image NAME    Set Docker image name (default: $IMAGE_NAME)"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 --server https://orchestrator.example.com --tenant abc123"
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -s|--server)
            SERVER_URL="$2"
            shift
            shift
            ;;
        -t|--tenant)
            TENANT_ID="$2"
            shift
            shift
            ;;
        -i|--image)
            IMAGE_NAME="$2"
            shift
            shift
            ;;
        -h|--help)
            show_help
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            ;;
    esac
done

# Validate server URL
if [ "$SERVER_URL" == "https://your-orchestrator-server" ]; then
    echo "ERROR: Please provide a real server URL, not the placeholder."
    echo "Example: $0 --server https://orchestrator.example.com --tenant abc123"
    exit 1
fi

# Validate tenant ID
if [ "$TENANT_ID" == "your-tenant-id" ]; then
    echo "ERROR: Please provide a real tenant ID, not the placeholder."
    echo "Example: $0 --server https://orchestrator.example.com --tenant abc123"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed or not in your PATH."
    echo "Please install Docker and try again."
    exit 1
fi

# Build Docker image
echo "Building Docker image..."
docker build -t $IMAGE_NAME -f agent/Dockerfile .

# Run Docker container
echo "Running agent with server: $SERVER_URL and tenant: $TENANT_ID"
docker run --rm \
    -e SERVER_URL="$SERVER_URL" \
    -e TENANT_ID="$TENANT_ID" \
    $IMAGE_NAME \
    --server "$SERVER_URL" \
    --tenant "$TENANT_ID"