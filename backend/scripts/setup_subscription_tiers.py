#!/usr/bin/env python
"""
Setup script for creating default subscription tiers

This script creates the default subscription tiers (free, standard, professional, enterprise)
for the orchestration platform.
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.initial_data import create_subscription_tiers

def main():
    """Initialize the database with default subscription tiers."""
    parser = argparse.ArgumentParser(description="Create default subscription tiers")
    args = parser.parse_args()
    
    db = SessionLocal()
    try:
        print("Creating default subscription tiers...")
        create_subscription_tiers(db)
        print("Subscription tiers created successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    main()