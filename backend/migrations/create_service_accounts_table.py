#!/usr/bin/env python
"""
Migration script to create service_accounts table if it doesn't exist
and ensure all required columns are present.
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Add parent directory to path to access app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings

def run_migration():
    """Run the migration to create or update service_accounts table."""
    print("Starting migration for service_accounts table...")
    
    # Create engine
    engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    
    # Check if table exists and create it if it doesn't
    with engine.connect() as connection:
        print("Checking if service_accounts table exists...")
        result = connection.execute(text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
            "WHERE table_name = 'service_accounts')"
        ))
        table_exists = result.scalar()
        
        if not table_exists:
            print("Creating service_accounts table...")
            connection.execute(text('''
                CREATE TABLE service_accounts (
                    account_id UUID PRIMARY KEY,
                    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
                    username VARCHAR(255) NOT NULL,
                    display_name VARCHAR(255) NOT NULL,
                    description TEXT,
                    account_type VARCHAR(50) NOT NULL DEFAULT 'robot',
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    created_by UUID REFERENCES users(user_id),
                    last_used TIMESTAMP WITH TIME ZONE,
                    configuration JSONB,
                    hashed_password VARCHAR(255)
                )
            '''))
            connection.commit()
            print("service_accounts table created successfully!")
        else:
            print("service_accounts table already exists, checking columns...")
            
            # List of columns that should exist in the table
            required_columns = [
                "account_id", "tenant_id", "username", "display_name", 
                "description", "account_type", "status", "created_at", 
                "updated_at", "created_by", "last_used", "configuration", 
                "hashed_password"
            ]
            
            # Check and add any missing columns
            for column in required_columns:
                result = connection.execute(text(
                    f"SELECT EXISTS (SELECT 1 FROM information_schema.columns "
                    f"WHERE table_name = 'service_accounts' AND column_name = '{column}')"
                ))
                column_exists = result.scalar()
                
                if not column_exists:
                    print(f"Adding missing column {column} to service_accounts table...")
                    
                    # Determine data type for the column
                    if column in ["account_id", "tenant_id", "created_by"]:
                        data_type = "UUID"
                    elif column in ["username", "display_name", "account_type", "status", "hashed_password"]:
                        data_type = "VARCHAR(255)"
                    elif column in ["description"]:
                        data_type = "TEXT"
                    elif column in ["created_at", "updated_at", "last_used"]:
                        data_type = "TIMESTAMP WITH TIME ZONE"
                    elif column in ["configuration"]:
                        data_type = "JSONB"
                    else:
                        data_type = "VARCHAR(255)"  # Default
                    
                    # Add the column
                    connection.execute(text(
                        f"ALTER TABLE service_accounts ADD COLUMN {column} {data_type}"
                    ))
                    connection.commit()
                    print(f"Column {column} added successfully!")
            
    print("Migration completed successfully!")

if __name__ == "__main__":
    run_migration()