#!/usr/bin/env python
"""
Migration script to add api_key column to agents table.
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Add parent directory to path to access app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings

def run_migration():
    """Run the migration to add api_key column to agents table."""
    print("Starting migration to add api_key column to agents table...")
    
    # Create engine
    engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    
    # Add column if it doesn't exist
    with engine.connect() as connection:
        print("Checking if api_key column exists...")
        result = connection.execute(text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'agents' AND column_name = 'api_key')"
        ))
        column_exists = result.scalar()
        
        if not column_exists:
            print("Adding api_key column to agents table...")
            connection.execute(text(
                "ALTER TABLE agents "
                "ADD COLUMN api_key VARCHAR(255)"
            ))
            connection.commit()
            print("Column added successfully!")
        else:
            print("Column api_key already exists. No migration needed.")
            
    print("Migration completed successfully!")

if __name__ == "__main__":
    run_migration()