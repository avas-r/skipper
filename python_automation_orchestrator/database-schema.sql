-- First, enable the UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Multi-tenancy Tables
CREATE TABLE tenants (
    tenant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    subscription_tier VARCHAR(20) NOT NULL DEFAULT 'standard',
    max_concurrent_jobs INT NOT NULL DEFAULT 50,
    max_agents INT NOT NULL DEFAULT 10,
    settings JSONB
);

-- User and Authentication Tables
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'active'
);

CREATE TABLE roles (
    role_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, name)
);

CREATE TABLE permissions (
    permission_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (resource, action)
);

CREATE TABLE role_permissions (
    role_id UUID NOT NULL REFERENCES roles(role_id),
    permission_id UUID NOT NULL REFERENCES permissions(permission_id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE user_roles (
    user_id UUID NOT NULL REFERENCES users(user_id),
    role_id UUID NOT NULL REFERENCES roles(role_id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, role_id)
);

-- Service robot accounts table for auto-login
CREATE TABLE service_accounts (
    account_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    username VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    account_type VARCHAR(50) NOT NULL DEFAULT 'robot',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id),
    last_used TIMESTAMP,
    configuration JSONB,
    UNIQUE (tenant_id, username)
);

-- Agent Management Tables
CREATE TABLE agents (
    agent_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    name VARCHAR(255) NOT NULL,
    machine_id VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45),
    status VARCHAR(20) NOT NULL DEFAULT 'offline',
    last_heartbeat TIMESTAMP,
    version VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    capabilities JSONB,
    tags JSONB,
    settings JSONB,
    service_account_id UUID REFERENCES service_accounts(account_id),
    session_type VARCHAR(50),
    auto_login_enabled BOOLEAN DEFAULT FALSE,
    session_status VARCHAR(50),
    UNIQUE (tenant_id, name)
);

CREATE TABLE agent_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(agent_id),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    log_level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB
);

-- Session monitoring table
CREATE TABLE agent_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(agent_id),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    service_account_id UUID REFERENCES service_accounts(account_id),
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMP,
    metadata JSONB
);

-- Asset Management Tables
CREATE TABLE asset_types (
    asset_type_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE asset_folders (
    folder_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    name VARCHAR(255) NOT NULL,
    parent_folder_id UUID REFERENCES asset_folders(folder_id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id),
    UNIQUE (tenant_id, name, parent_folder_id)
);

CREATE TABLE assets (
    asset_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    asset_type_id UUID NOT NULL REFERENCES asset_types(asset_type_id),
    folder_id UUID REFERENCES asset_folders(folder_id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_encrypted BOOLEAN NOT NULL DEFAULT TRUE,
    value TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id),
    updated_by UUID REFERENCES users(user_id),
    version INT NOT NULL DEFAULT 1,
    UNIQUE (tenant_id, name)
);

CREATE TABLE asset_permissions (
    asset_id UUID NOT NULL REFERENCES assets(asset_id),
    role_id UUID NOT NULL REFERENCES roles(role_id),
    can_view BOOLEAN NOT NULL DEFAULT FALSE,
    can_edit BOOLEAN NOT NULL DEFAULT FALSE,
    can_delete BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (asset_id, role_id)
);

-- Queue Management Tables
CREATE TABLE queues (
    queue_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    max_retries INT NOT NULL DEFAULT 3,
    retry_delay_seconds INT NOT NULL DEFAULT 60,
    priority INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    settings JSONB,
    UNIQUE (tenant_id, name)
);

CREATE TABLE queue_items (
    item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    queue_id UUID NOT NULL REFERENCES queues(queue_id),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    priority INT NOT NULL DEFAULT 1,
    reference_id VARCHAR(255),
    payload JSONB NOT NULL,
    processing_time_ms INT,
    retry_count INT NOT NULL DEFAULT 0,
    next_processing_time TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMP,
    error_message TEXT,
    assigned_to UUID REFERENCES agents(agent_id),
    due_date TIMESTAMP
);

-- Process/Package Management Tables
CREATE TABLE packages (
    package_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id),
    updated_by UUID REFERENCES users(user_id),
    status VARCHAR(20) NOT NULL DEFAULT 'development',
    main_file_path VARCHAR(255) NOT NULL,
    storage_path VARCHAR(255) NOT NULL,
    entry_point VARCHAR(255) NOT NULL,
    md5_hash VARCHAR(32),
    dependencies JSONB,
    tags JSONB,
    UNIQUE (tenant_id, name, version)
);

CREATE TABLE package_permissions (
    package_id UUID NOT NULL REFERENCES packages(package_id),
    role_id UUID NOT NULL REFERENCES roles(role_id),
    can_view BOOLEAN NOT NULL DEFAULT FALSE,
    can_execute BOOLEAN NOT NULL DEFAULT FALSE,
    can_edit BOOLEAN NOT NULL DEFAULT FALSE, 
    can_delete BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (package_id, role_id)
);

-- Scheduling Tables
CREATE TABLE schedules (
    schedule_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    cron_expression VARCHAR(100) NOT NULL,
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id),
    updated_by UUID REFERENCES users(user_id),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    last_execution TIMESTAMP,
    next_execution TIMESTAMP,
    UNIQUE (tenant_id, name)
);

-- Job Management Tables
CREATE TABLE jobs (
    job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    package_id UUID NOT NULL REFERENCES packages(package_id),
    schedule_id UUID REFERENCES schedules(schedule_id),
    queue_id UUID REFERENCES queues(queue_id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    priority INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id),
    max_concurrent_runs INT NOT NULL DEFAULT 1,
    timeout_seconds INT NOT NULL DEFAULT 3600,
    retry_count INT NOT NULL DEFAULT 0,
    retry_delay_seconds INT NOT NULL DEFAULT 60,
    parameters JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    UNIQUE (tenant_id, name)
);

CREATE TABLE job_executions (
    execution_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(job_id),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    agent_id UUID REFERENCES agents(agent_id),
    queue_item_id UUID REFERENCES queue_items(item_id),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    execution_time_ms INT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    input_parameters JSONB,
    output_results JSONB,
    error_message TEXT,
    logs_path VARCHAR(255),
    screenshots_path VARCHAR(255),
    recording_path VARCHAR(255),
    trigger_type VARCHAR(50) NOT NULL
);

CREATE TABLE job_dependencies (
    job_id UUID NOT NULL REFERENCES jobs(job_id),
    depends_on_job_id UUID NOT NULL REFERENCES jobs(job_id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (job_id, depends_on_job_id)
);

-- Notification System Tables
CREATE TABLE notification_types (
    type_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE notification_channels (
    channel_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,  -- email, slack, webhook, etc.
    configuration JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    UNIQUE (tenant_id, name)
);

CREATE TABLE notification_rules (
    rule_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    name VARCHAR(255) NOT NULL,
    notification_type_id UUID NOT NULL REFERENCES notification_types(type_id),
    channel_id UUID NOT NULL REFERENCES notification_channels(channel_id),
    conditions JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    UNIQUE (tenant_id, name)
);

CREATE TABLE notifications (
    notification_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    rule_id UUID NOT NULL REFERENCES notification_rules(rule_id),
    subject VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    sent_at TIMESTAMP,
    reference_id UUID,
    reference_type VARCHAR(50),
    metadata JSONB
);

-- Audit Logs
CREATE TABLE audit_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    user_id UUID REFERENCES users(user_id),
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    details JSONB,
    ip_address VARCHAR(45)
);

-- Add permissions for service accounts management
INSERT INTO permissions (name, description, resource, action)
VALUES 
    ('service_accounts:create', 'Create service accounts', 'service_accounts', 'create'),
    ('service_accounts:read', 'View service accounts', 'service_accounts', 'read'),
    ('service_accounts:update', 'Update service accounts', 'service_accounts', 'update'),
    ('service_accounts:delete', 'Delete service accounts', 'service_accounts', 'delete'),
    ('service_accounts:read_credentials', 'View service account credentials', 'service_accounts', 'read_credentials');

-- Add audit log types for service account operations
INSERT INTO notification_types (name, description)
VALUES
    ('service_account_created', 'Service account created'),
    ('service_account_updated', 'Service account updated'),
    ('service_account_deleted', 'Service account deleted'),
    ('service_account_credentials_accessed', 'Service account credentials accessed'),
    ('auto_login_configured', 'Auto-login configured for an agent'),
    ('auto_login_failed', 'Auto-login failed for an agent');

-- Indexes for performance
CREATE INDEX idx_queue_items_status ON queue_items(status);
CREATE INDEX idx_queue_items_tenant ON queue_items(tenant_id);
CREATE INDEX idx_job_executions_status ON job_executions(status);
CREATE INDEX idx_job_executions_tenant ON job_executions(tenant_id);
CREATE INDEX idx_audit_logs_tenant_action ON audit_logs(tenant_id, action);
CREATE INDEX idx_assets_tenant ON assets(tenant_id);
CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_agents_tenant ON agents(tenant_id);
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_service_accounts_tenant ON service_accounts(tenant_id);
CREATE INDEX idx_agents_service_account ON agents(service_account_id);
CREATE INDEX idx_agents_session_type ON agents(session_type);
CREATE INDEX idx_agent_sessions_agent ON agent_sessions(agent_id);
CREATE INDEX idx_agent_sessions_tenant ON agent_sessions(tenant_id);
CREATE INDEX idx_agent_sessions_status ON agent_sessions(status);



-- Drop tables in reverse order of their dependencies
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS notification_rules;
DROP TABLE IF EXISTS notification_channels;
DROP TABLE IF EXISTS notification_types;
DROP TABLE IF EXISTS job_dependencies;
DROP TABLE IF EXISTS job_executions;
DROP TABLE IF EXISTS jobs;
DROP TABLE IF EXISTS schedules;
DROP TABLE IF EXISTS package_permissions;
DROP TABLE IF EXISTS packages;
DROP TABLE IF EXISTS queue_items;
DROP TABLE IF EXISTS queues;
DROP TABLE IF EXISTS asset_permissions;
DROP TABLE IF EXISTS assets;
DROP TABLE IF EXISTS asset_folders;
DROP TABLE IF EXISTS asset_types;
DROP TABLE IF EXISTS agent_sessions;
DROP TABLE IF EXISTS agent_logs;
DROP TABLE IF EXISTS agents;
DROP TABLE IF EXISTS service_accounts;
DROP TABLE IF EXISTS user_roles;
DROP TABLE IF EXISTS role_permissions;
DROP TABLE IF EXISTS permissions;
DROP TABLE IF EXISTS roles;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS tenants;