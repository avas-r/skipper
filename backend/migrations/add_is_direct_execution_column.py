#!/usr/bin/env python
"""
Migration script to add is_direct_execution column to job_executions table.
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Add parent directory to path to access app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings

def run_migration():
    """Run the migration to add is_direct_execution column to job_executions table."""
    print("Starting migration to add is_direct_execution column to job_executions table...")
    
    # Create engine
    engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    
    # Add column if it doesn't exist
    with engine.connect() as connection:
        print("Checking if job_executions table exists...")
        result = connection.execute(text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
            "WHERE table_name = 'job_executions')"
        ))
        table_exists = result.scalar()
        
        if not table_exists:
            print("Table job_executions doesn't exist. Creating table...")
            connection.execute(text('''
                CREATE TABLE job_executions (
                    execution_id UUID PRIMARY KEY,
                    job_id UUID REFERENCES jobs(job_id),
                    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
                    agent_id UUID REFERENCES agents(agent_id),
                    queue_item_id UUID REFERENCES queue_items(item_id),
                    status VARCHAR(50) NOT NULL,
                    trigger_type VARCHAR(50),
                    started_at TIMESTAMP WITH TIME ZONE,
                    completed_at TIMESTAMP WITH TIME ZONE,
                    execution_time_ms INTEGER,
                    input_parameters JSONB,
                    output_results JSONB,
                    error_message TEXT,
                    logs_path VARCHAR(255),
                    screenshots_path VARCHAR(255),
                    recording_path VARCHAR(255),
                    is_direct_execution BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                )
            '''))
            connection.commit()
            print("Table job_executions created with is_direct_execution column!")
        else:
            # Check if column exists
            print("Checking if is_direct_execution column exists...")
            result = connection.execute(text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
                "WHERE table_name = 'job_executions' AND column_name = 'is_direct_execution')"
            ))
            column_exists = result.scalar()
            
            if not column_exists:
                print("Adding is_direct_execution column to job_executions table...")
                connection.execute(text(
                    "ALTER TABLE job_executions "
                    "ADD COLUMN is_direct_execution BOOLEAN DEFAULT FALSE"
                ))
                connection.commit()
                print("Column added successfully!")
            else:
                print("Column is_direct_execution already exists. No migration needed.")
            
    print("Migration completed successfully!")

if __name__ == "__main__":
    run_migration()