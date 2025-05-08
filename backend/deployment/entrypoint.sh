#!/bin/bash
set -e

# Wait for dependencies to be ready
/wait

# Run database migrations
alembic upgrade head

# Execute the command provided as arguments
exec "$@"