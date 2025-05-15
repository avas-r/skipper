#!/bin/bash
set -e

# This script initializes the PostgreSQL database for Skipper
# It will be executed automatically when the container starts

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  -- Create extensions
  CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
  CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
  
  -- Create schema
  CREATE SCHEMA IF NOT EXISTS skipper;
  
  -- Create tables
  CREATE TABLE IF NOT EXISTS skipper.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
  );
  
  CREATE TABLE IF NOT EXISTS skipper.agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(64) UNIQUE NOT NULL,
    agent_type VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'offline',
    capabilities JSONB NOT NULL DEFAULT '{}',
    metadata JSONB NOT NULL DEFAULT '{}',
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
  );
  
  CREATE TABLE IF NOT EXISTS skipper.tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    priority INTEGER NOT NULL DEFAULT 0,
    created_by UUID REFERENCES skipper.users(id),
    assigned_to UUID REFERENCES skipper.agents(id),
    parameters JSONB NOT NULL DEFAULT '{}',
    result JSONB,
    error_message TEXT,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
  );
  
  CREATE TABLE IF NOT EXISTS skipper.audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES skipper.users(id),
    agent_id UUID REFERENCES skipper.agents(id),
    action VARCHAR(64) NOT NULL,
    resource_type VARCHAR(64) NOT NULL,
    resource_id VARCHAR(64) NOT NULL,
    details JSONB NOT NULL DEFAULT '{}',
    ip_address VARCHAR(45),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
  );
  
  -- Create indexes
  CREATE INDEX IF NOT EXISTS idx_tasks_status ON skipper.tasks(status);
  CREATE INDEX IF NOT EXISTS idx_tasks_priority ON skipper.tasks(priority);
  CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON skipper.tasks(assigned_to);
  CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON skipper.audit_logs(action);
  CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_type ON skipper.audit_logs(resource_type);
  CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_id ON skipper.audit_logs(resource_id);
  
  -- Create admin user (username: admin, password: admin)
  INSERT INTO skipper.users (username, email, password_hash, is_admin)
  VALUES ('admin', 'admin@example.com', '\$2b\$12\$jTM09Nm1UPp25uXnvsn8Xu9NnqEYJa56Zwwhk8PWaLCtBJVcz.oQy', TRUE)
  ON CONFLICT (username) DO NOTHING;
  
  -- Grant privileges
  GRANT ALL PRIVILEGES ON SCHEMA skipper TO skipper;
  GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA skipper TO skipper;
  GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA skipper TO skipper;
EOSQL

# Create metrics user for monitoring
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  -- Create readonly user for monitoring
  CREATE USER postgres_exporter WITH PASSWORD 'monitoring';
  GRANT pg_monitor TO postgres_exporter;
  ALTER USER postgres_exporter SET SEARCH_PATH TO postgres_exporter,pg_catalog;
EOSQL

echo "PostgreSQL initialization completed"