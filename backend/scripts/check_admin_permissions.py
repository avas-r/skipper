#!/usr/bin/env python
"""
Script to check and fix admin role permissions.
"""

import sys
from pathlib import Path
import uuid

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.models.user import Role, Permission, RolePermission

# Create a database session
db = SessionLocal()

def check_admin_permissions():
    """Check admin role permissions and add missing ones."""
    # Get admin role
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if not admin_role:
        print("Admin role not found!")
        return
    
    print(f"Found admin role with ID: {admin_role.role_id}")
    
    # Get all agent permissions
    agent_permissions = db.query(Permission).filter(
        Permission.resource == "agent"
    ).all()
    
    agent_perm_ids = set(p.permission_id for p in agent_permissions)
    print(f"Found {len(agent_permissions)} agent permissions")
    
    # Get current role permissions
    current_perms = db.query(RolePermission).filter(
        RolePermission.role_id == admin_role.role_id
    ).all()
    
    current_perm_ids = set(rp.permission_id for rp in current_perms)
    
    # Find missing agent permissions
    missing_perm_ids = agent_perm_ids - current_perm_ids
    
    if not missing_perm_ids:
        print("Admin role has all agent permissions!")
        return
        
    # Add missing permissions to admin role
    for perm_id in missing_perm_ids:
        perm = db.query(Permission).filter(Permission.permission_id == perm_id).first()
        print(f"Adding permission {perm.name} to admin role")
        
        role_perm = RolePermission(
            role_id=admin_role.role_id,
            permission_id=perm_id,
        )
        db.add(role_perm)
    
    db.commit()
    print("Admin permissions updated successfully!")

if __name__ == "__main__":
    check_admin_permissions()
    db.close()