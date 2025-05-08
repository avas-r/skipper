# Database Schema Design

## Overview

The database schema is designed with a multi-tenant architecture, using PostgreSQL as the database engine. The schema follows these key principles:

1. **Multi-tenancy**: All entities have a tenant_id reference for complete data isolation
2. **Comprehensive auditing**: Audit logs for all significant operations
3. **Optimized queries**: Indexes for common access patterns
4. **Flexibility**: JSON fields for extensible metadata
5. **Security**: Encrypted storage for sensitive data
6. **Referential integrity**: Foreign key relationships between related entities

## Core Tables

### Tenant Management

```sql
CREATE TABLE tenants (
    tenant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active, suspended, pending, archived
    subscription_tier VARCHAR(20) NOT NULL DEFAULT 'standard', -- free, standard, professional, enterprise
    max_concurrent_jobs INT NOT NULL DEFAULT 50,
    max_agents INT NOT NULL DEFAULT 10,
    settings JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE subscription_tiers (
    tier_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    price_monthly FLOAT NOT NULL DEFAULT 0.0,
    price_yearly FLOAT NOT NULL DEFAULT 0.0,
    is_public BOOLEAN NOT NULL DEFAULT true,
    max_agents INT NOT NULL,
    max_concurrent_jobs INT NOT NULL,
    max_schedules INT NOT NULL,
    max_queues INT NOT NULL,
    storage_gb INT NOT NULL DEFAULT 5,
    max_api_calls_daily INT NOT NULL DEFAULT 1000,
    enable_api_access BOOLEAN NOT NULL DEFAULT true,
    enable_schedules BOOLEAN NOT NULL DEFAULT true,
    enable_queues BOOLEAN NOT NULL DEFAULT true,
    enable_analytics BOOLEAN NOT NULL DEFAULT false,
    enable_custom_branding BOOLEAN NOT NULL DEFAULT false,
    enable_sla_support BOOLEAN NOT NULL DEFAULT false,
    enable_audit_logs BOOLEAN NOT NULL DEFAULT false,
    features JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE tenant_subscriptions (
    subscription_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    tier_id UUID NOT NULL REFERENCES subscription_tiers(tier_id),
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active, canceled, past_due, trialing
    billing_cycle VARCHAR(10) NOT NULL DEFAULT 'monthly', -- monthly, yearly
    start_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    end_date TIMESTAMP WITH TIME ZONE, -- Null for auto-renewing subscriptions
    trial_end_date TIMESTAMP WITH TIME ZONE,
    last_billing_date TIMESTAMP WITH TIME ZONE,
    next_billing_date TIMESTAMP WITH TIME ZONE,
    canceled_at TIMESTAMP WITH TIME ZONE,
    price_override FLOAT, -- Custom pricing if applicable
    max_agents_override INT, -- Custom resource limits if applicable
    max_concurrent_jobs_override INT,
    feature_overrides JSONB, -- Custom feature flags if applicable
    payment_provider VARCHAR(50), -- Payment provider (e.g., "stripe", "paypal")
    external_subscription_id VARCHAR(255), -- ID in payment provider's system
    external_customer_id VARCHAR(255), -- Customer ID in payment provider
    auto_renew BOOLEAN NOT NULL DEFAULT true,
    is_trial BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

### User Management and Authentication

```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active, inactive, pending, locked
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

CREATE TABLE permissions (
    permission_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    resource VARCHAR(100) NOT NULL, -- 'job', 'agent', etc.
    action VARCHAR(50) NOT NULL, -- 'read', 'write', 'execute', 'delete'
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(resource, action)
);

CREATE TABLE roles (
    role_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(tenant_id, name)
);

CREATE TABLE role_permissions (
    role_id UUID REFERENCES roles(role_id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(permission_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE user_roles (
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(role_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, role_id)
);

-- Service Accounts for agent auto-login
CREATE TABLE service_accounts (
    account_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    username VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    account_type VARCHAR(50) NOT NULL DEFAULT 'robot', -- robot, service
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active, inactive, locked
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id),
    last_used TIMESTAMP WITH TIME ZONE,
    configuration JSONB,
    hashed_password VARCHAR(255), -- Encrypted password storage
    UNIQUE(tenant_id, username)
);

-- Agent Management
CREATE TABLE agents (
    agent_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    machine_id VARCHAR(255) NOT NULL, -- Unique identifier for the machine
    ip_address INET,
    api_key VARCHAR(255), -- Key for agent authentication
    status VARCHAR(20) NOT NULL DEFAULT 'offline', -- online, offline, busy
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    version VARCHAR(50),
    capabilities JSONB, -- Agent capabilities (Python version, installed libs, etc.)
    tags JSONB, -- Tags for agent grouping and filtering
    settings JSONB, -- Additional settings
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    -- Auto-login related fields
    service_account_id UUID REFERENCES service_accounts(account_id),
    session_type VARCHAR(50),
    auto_login_enabled BOOLEAN DEFAULT FALSE,
    session_status VARCHAR(50),
    UNIQUE(tenant_id, machine_id)
);

-- Agent Sessions
CREATE TABLE agent_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    service_account_id UUID REFERENCES service_accounts(account_id),
    status VARCHAR(50) NOT NULL, -- active, ended, terminated, failed
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB -- Additional session information
);

-- Agent Logs
CREATE TABLE agent_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    log_level VARCHAR(20) NOT NULL, -- info, warning, error, debug
    message TEXT NOT NULL,
    metadata JSONB, -- Additional log information
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Schedules
CREATE TABLE schedules (
    schedule_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    job_id UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    cron_expression VARCHAR(100) NOT NULL, -- Cron expression for schedule
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC', -- Timezone for schedule
    parameters JSONB, -- Override job parameters
    start_date TIMESTAMP WITH TIME ZONE, -- Optional start date
    end_date TIMESTAMP WITH TIME ZONE, -- Optional end date
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active, paused, completed
    last_run_time TIMESTAMP WITH TIME ZONE, -- Last execution time
    next_run_time TIMESTAMP WITH TIME ZONE, -- Next scheduled execution time
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id),
    updated_by UUID REFERENCES users(user_id)
);

-- Queue Management
CREATE TABLE queues (
    queue_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    job_id UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE, -- Job to process queue items
    max_retries INT NOT NULL DEFAULT 3, -- Maximum retries for failed items
    retry_delay_seconds INT NOT NULL DEFAULT 300, -- Delay between retries
    timeout_seconds INT NOT NULL DEFAULT 3600, -- Processing timeout
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active, paused, stopped
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id),
    updated_by UUID REFERENCES users(user_id),
    UNIQUE(tenant_id, name)
);

-- Queue Items
CREATE TABLE queue_items (
    item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    queue_id UUID NOT NULL REFERENCES queues(queue_id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'new', -- new, processing, completed, failed, retrying
    priority INT NOT NULL DEFAULT 1, -- Item priority (higher = more important)
    reference_id VARCHAR(255), -- External reference ID
    specific_data JSONB, -- Item-specific data
    processing_attempts INT NOT NULL DEFAULT 0, -- Number of processing attempts
    last_processing_time TIMESTAMP WITH TIME ZONE, -- Last processing time
    next_retry_time TIMESTAMP WITH TIME ZONE, -- Next retry time if failed
    result_data JSONB, -- Processing result
    error_message TEXT, -- Error message if failed
    execution_id UUID REFERENCES job_executions(execution_id), -- Reference to job execution
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id)
);

-- Asset Types
CREATE TABLE asset_types (
    type_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    schema JSONB, -- JSON schema for validation
    encryption_required BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Asset Folders
CREATE TABLE asset_folders (
    folder_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    parent_folder_id UUID REFERENCES asset_folders(folder_id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id),
    updated_by UUID REFERENCES users(user_id),
    UNIQUE(tenant_id, name, parent_folder_id)
);

-- Assets
CREATE TABLE assets (
    asset_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    folder_id UUID REFERENCES asset_folders(folder_id),
    type_id UUID NOT NULL REFERENCES asset_types(type_id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    value_encrypted BYTEA, -- Encrypted asset value
    value_json JSONB, -- Non-sensitive asset values
    is_shared BOOLEAN NOT NULL DEFAULT FALSE, -- Whether asset is shared with other tenants
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id),
    updated_by UUID REFERENCES users(user_id),
    UNIQUE(tenant_id, name, folder_id)
);

-- Asset Permissions
CREATE TABLE asset_permissions (
    asset_id UUID NOT NULL REFERENCES assets(asset_id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(role_id) ON DELETE CASCADE,
    can_view BOOLEAN NOT NULL DEFAULT FALSE,
    can_edit BOOLEAN NOT NULL DEFAULT FALSE,
    can_delete BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    PRIMARY KEY (asset_id, role_id)
);

-- Notification Types
CREATE TABLE notification_types (
    type_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    default_template TEXT, -- Default notification template
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Notification Channels
CREATE TABLE notification_channels (
    channel_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL, -- email, slack, webhook, sms, etc.
    configuration JSONB NOT NULL, -- Channel-specific configuration
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id),
    updated_by UUID REFERENCES users(user_id),
    UNIQUE(tenant_id, name)
);

-- Notification Rules
CREATE TABLE notification_rules (
    rule_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type_id UUID NOT NULL REFERENCES notification_types(type_id),
    condition JSONB NOT NULL, -- Condition for triggering notification
    template_override TEXT, -- Optional template override
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id),
    updated_by UUID REFERENCES users(user_id)
);

-- Notification Rule Channels
CREATE TABLE notification_rule_channels (
    rule_id UUID NOT NULL REFERENCES notification_rules(rule_id) ON DELETE CASCADE,
    channel_id UUID NOT NULL REFERENCES notification_channels(channel_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    PRIMARY KEY (rule_id, channel_id)
);

-- Notifications
CREATE TABLE notifications (
    notification_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    rule_id UUID REFERENCES notification_rules(rule_id),
    type_id UUID NOT NULL REFERENCES notification_types(type_id),
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL, -- info, warning, error, critical
    entity_type VARCHAR(50), -- Type of entity that triggered notification
    entity_id UUID, -- ID of entity that triggered notification
    metadata JSONB, -- Additional notification data
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    read_by UUID REFERENCES users(user_id),
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Audit Logs
CREATE TABLE audit_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(user_id),
    action VARCHAR(255) NOT NULL, -- Action performed
    entity_type VARCHAR(50) NOT NULL, -- Type of entity acted upon
    entity_id UUID, -- ID of entity acted upon
    details JSONB, -- Additional log details
    ip_address INET, -- IP address of the user
    user_agent TEXT, -- User agent information
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Creating indexes for common query patterns
CREATE INDEX idx_job_executions_job_id ON job_executions(job_id);
CREATE INDEX idx_job_executions_agent_id ON job_executions(agent_id);
CREATE INDEX idx_job_executions_status ON job_executions(status);
CREATE INDEX idx_job_executions_tenant_id ON job_executions(tenant_id);
CREATE INDEX idx_job_executions_created_at ON job_executions(created_at);

CREATE INDEX idx_queue_items_queue_id ON queue_items(queue_id);
CREATE INDEX idx_queue_items_status ON queue_items(status);
CREATE INDEX idx_queue_items_priority ON queue_items(priority);
CREATE INDEX idx_queue_items_tenant_id ON queue_items(tenant_id);
CREATE INDEX idx_queue_items_reference_id ON queue_items(reference_id);

CREATE INDEX idx_agents_tenant_id ON agents(tenant_id);
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_last_heartbeat ON agents(last_heartbeat);

CREATE INDEX idx_packages_tenant_id_name ON packages(tenant_id, name);
CREATE INDEX idx_packages_status ON packages(status);

CREATE INDEX idx_schedules_tenant_id ON schedules(tenant_id);
CREATE INDEX idx_schedules_next_run_time ON schedules(next_run_time);
CREATE INDEX idx_schedules_status ON schedules(status);

CREATE INDEX idx_notifications_tenant_id ON notifications(tenant_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);

CREATE INDEX idx_audit_logs_tenant_id ON audit_logs(tenant_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_entity_type_id ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- Create trigger function for updating updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$ LANGUAGE 'plpgsql';

-- Apply triggers to all tables with updated_at columns
CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_roles_updated_at BEFORE UPDATE ON roles FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_packages_updated_at BEFORE UPDATE ON packages FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON jobs FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_schedules_updated_at BEFORE UPDATE ON schedules FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_queues_updated_at BEFORE UPDATE ON queues FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_queue_items_updated_at BEFORE UPDATE ON queue_items FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_service_accounts_updated_at BEFORE UPDATE ON service_accounts FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_job_executions_updated_at BEFORE UPDATE ON job_executions FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- Package Management
CREATE TABLE packages (
    package_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(50) NOT NULL,
    main_file_path VARCHAR(255) NOT NULL, -- Path to main file
    storage_path VARCHAR(255) NOT NULL, -- Storage path for package files
    entry_point VARCHAR(255) NOT NULL, -- Entry point for execution
    md5_hash VARCHAR(32), -- MD5 hash for integrity verification
    dependencies JSONB, -- Package dependencies
    tags JSONB, -- Tags for filtering
    status VARCHAR(20) NOT NULL DEFAULT 'development', -- development, testing, production, deprecated
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id),
    updated_by UUID REFERENCES users(user_id),
    UNIQUE(tenant_id, name, version)
);

-- Package Permissions
CREATE TABLE package_permissions (
    package_id UUID NOT NULL REFERENCES packages(package_id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(role_id) ON DELETE CASCADE,
    can_view BOOLEAN NOT NULL DEFAULT FALSE,
    can_execute BOOLEAN NOT NULL DEFAULT FALSE,
    can_edit BOOLEAN NOT NULL DEFAULT FALSE,
    can_delete BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    PRIMARY KEY (package_id, role_id)
);

-- Jobs
CREATE TABLE jobs (
    job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    package_id UUID REFERENCES packages(package_id),
    parameters JSONB, -- Job parameters
    timeout_seconds INT NOT NULL DEFAULT 3600, -- Job timeout in seconds
    retry_count INT NOT NULL DEFAULT 0, -- Number of retries on failure
    retry_delay_seconds INT NOT NULL DEFAULT 300, -- Delay between retries
    priority INT NOT NULL DEFAULT 1, -- Job priority (higher = more important)
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active, paused, archived
    tags JSONB, -- Tags for filtering
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id),
    updated_by UUID REFERENCES users(user_id)
);

-- Job Dependencies
CREATE TABLE job_dependencies (
    job_id UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    depends_on_job_id UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    PRIMARY KEY (job_id, depends_on_job_id),
    CHECK (job_id <> depends_on_job_id) -- Prevent self-dependency
);

-- Job Executions
CREATE TABLE job_executions (
    execution_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(agent_id),
    package_id UUID REFERENCES packages(package_id),
    status VARCHAR(20) NOT NULL, -- queued, running, completed, failed, canceled
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    parameters JSONB, -- Execution parameters
    result_data JSONB, -- Execution results
    result_files JSONB, -- Paths to result files
    error_message TEXT, -- Error message if failed
    error_details JSONB, -- Detailed error information
    retry_count INT NOT NULL DEFAULT 0, -- Current retry count
    parent_execution_id UUID REFERENCES job_executions(execution_id), -- For retry chains
    triggered_by VARCHAR(50), -- manual, schedule, queue, api
    triggered_by_id UUID, -- Reference to schedule or queue item ID
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Job Execution Logs
CREATE TABLE job_execution_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id UUID NOT NULL REFERENCES job_executions(execution_id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    log_level VARCHAR(20) NOT NULL, -- info, warning, error, debug
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);