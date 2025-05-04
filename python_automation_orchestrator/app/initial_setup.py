#!/usr/bin/env python
"""
Initial Setup Script for Python Automation Orchestrator

This script creates an initial admin user and tenant when setting up
the orchestrator for the first time.
"""

import sys
import uuid
import argparse
from datetime import datetime
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import engine, SessionLocal
from app.models.tenant import Tenant
from app.models.user import User, Role, Permission
from app.auth.auth import get_password_hash
import sqlalchemy as sa
from sqlalchemy.orm import Session

def create_initial_permissions(db: Session):
    """Create basic permissions"""
    print("Creating permissions...")
    
    # Define basic permissions
    permissions = [
        # Tenant permissions
        {"name": "tenant:read", "resource": "tenant", "action": "read", "description": "View tenant information"},
        {"name": "tenant:write", "resource": "tenant", "action": "write", "description": "Modify tenant settings"},
        
        # User permissions
        {"name": "user:read", "resource": "user", "action": "read", "description": "View user information"},
        {"name": "user:write", "resource": "user", "action": "write", "description": "Create/modify users"},
        {"name": "user:delete", "resource": "user", "action": "delete", "description": "Delete users"},
        
        # Role permissions
        {"name": "role:read", "resource": "role", "action": "read", "description": "View roles"},
        {"name": "role:write", "resource": "role", "action": "write", "description": "Create/modify roles"},
        {"name": "role:delete", "resource": "role", "action": "delete", "description": "Delete roles"},
        
        # Agent permissions
        {"name": "agent:read", "resource": "agent", "action": "read", "description": "View agents"},
        {"name": "agent:write", "resource": "agent", "action": "write", "description": "Modify agent settings"},
        {"name": "agent:delete", "resource": "agent", "action": "delete", "description": "Delete agents"},
        
        # Job permissions
        {"name": "job:read", "resource": "job", "action": "read", "description": "View jobs"},
        {"name": "job:write", "resource": "job", "action": "write", "description": "Create/modify jobs"},
        {"name": "job:delete", "resource": "job", "action": "delete", "description": "Delete jobs"},
        {"name": "job:execute", "resource": "job", "action": "execute", "description": "Execute jobs"},
        
        # Package permissions
        {"name": "package:read", "resource": "package", "action": "read", "description": "View packages"},
        {"name": "package:write", "resource": "package", "action": "write", "description": "Upload/modify packages"},
        {"name": "package:delete", "resource": "package", "action": "delete", "description": "Delete packages"},
        
        # Asset permissions
        {"name": "asset:read", "resource": "asset", "action": "read", "description": "View assets"},
        {"name": "asset:write", "resource": "asset", "action": "write", "description": "Create/modify assets"},
        {"name": "asset:delete", "resource": "asset", "action": "delete", "description": "Delete assets"},
        
        # Schedule permissions
        {"name": "schedule:read", "resource": "schedule", "action": "read", "description": "View schedules"},
        {"name": "schedule:write", "resource": "schedule", "action": "write", "description": "Create/modify schedules"},
        {"name": "schedule:delete", "resource": "schedule", "action": "delete", "description": "Delete schedules"},
        
        # Queue permissions
        {"name": "queue:read", "resource": "queue", "action": "read", "description": "View queues"},
        {"name": "queue:write", "resource": "queue", "action": "write", "description": "Create/modify queues"},
        {"name": "queue:delete", "resource": "queue", "action": "delete", "description": "Delete queues"}
    ]
    
    for perm_data in permissions:
        # Check if permission exists
        existing = db.query(Permission).filter(Permission.name == perm_data["name"]).first()
        if not existing:
            permission = Permission(
                permission_id=uuid.uuid4(),
                name=perm_data["name"],
                description=perm_data["description"],
                resource=perm_data["resource"],
                action=perm_data["action"]
            )
            db.add(permission)
    
    db.commit()
    return db.query(Permission).all()

def create_roles(db: Session, tenant_id: uuid.UUID, permissions: list):
    """Create admin and user roles"""
    print("Creating roles...")
    
    # Create admin role with all permissions
    admin_role = db.query(Role).filter(
        Role.name == "Admin",
        Role.tenant_id == tenant_id
    ).first()
    
    if not admin_role:
        admin_role = Role(
            role_id=uuid.uuid4(),
            tenant_id=tenant_id,
            name="Admin",
            description="Administrator with full access",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(admin_role)
        db.flush()
        
        # Assign all permissions to admin
        for permission in permissions:
            admin_role.permissions.append(permission)
    
    # Create user role with limited permissions
    user_role = db.query(Role).filter(
        Role.name == "User", 
        Role.tenant_id == tenant_id
    ).first()
    
    if not user_role:
        user_role = Role(
            role_id=uuid.uuid4(),
            tenant_id=tenant_id,
            name="User",
            description="Regular user with limited access",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(user_role)
        db.flush()
        
        # Assign read permissions to user role
        for permission in permissions:
            if ":read" in permission.name or permission.action == "read":
                user_role.permissions.append(permission)
    
    db.commit()
    return admin_role, user_role

def create_tenant(db: Session, name: str):
    """Create a new tenant"""
    print(f"Creating tenant: {name}")
    
    tenant = db.query(Tenant).filter(Tenant.name == name).first()
    if not tenant:
        tenant = Tenant(
            tenant_id=uuid.uuid4(),
            name=name,
            status="active",
            subscription_tier="standard",
            max_concurrent_jobs=50,
            max_agents=10,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    
    return tenant

def create_admin_user(db: Session, email: str, password: str, tenant_id: uuid.UUID, admin_role_id: uuid.UUID):
    """Create an admin user"""
    print(f"Creating admin user: {email}")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            user_id=uuid.uuid4(),
            tenant_id=tenant_id,
            email=email,
            hashed_password=get_password_hash(password),
            full_name="Administrator",
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(user)
        db.flush()
        
        # Add admin role to user
        admin_role = db.query(Role).filter(Role.role_id == admin_role_id).first()
        if admin_role:
            user.roles.append(admin_role)
        
        db.commit()
        db.refresh(user)
    
    return user

def main():
    parser = argparse.ArgumentParser(description="Initialize the orchestrator with first admin user and tenant")
    parser.add_argument("--admin-email", required=True, help="Admin user email")
    parser.add_argument("--admin-password", required=True, help="Admin user password")
    parser.add_argument("--tenant-name", default="Default Tenant", help="Tenant name")
    
    args = parser.parse_args()
    
    # Create tables if they don't exist
    from app.db.base import Base
    print("Creating database tables if they don't exist...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Create tenant
        tenant = create_tenant(db, args.tenant_name)
        print(f"Tenant created with ID: {tenant.tenant_id}")
        
        # Create permissions
        permissions = create_initial_permissions(db)
        print(f"Created {len(permissions)} permissions")
        
        # Create roles
        admin_role, user_role = create_roles(db, tenant.tenant_id, permissions)
        print(f"Created Admin role with ID: {admin_role.role_id}")
        print(f"Created User role with ID: {user_role.role_id}")
        
        # Create admin user
        admin_user = create_admin_user(db, args.admin_email, args.admin_password, tenant.tenant_id, admin_role.role_id)
        print(f"Created admin user with ID: {admin_user.user_id}")
        
        print("\nSetup complete!")
        print(f"Tenant ID: {tenant.tenant_id}")
        print(f"You can now run the agent with:")
        print(f"python run_agent.py --server http://your-server:8000 --tenant {tenant.tenant_id}")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()