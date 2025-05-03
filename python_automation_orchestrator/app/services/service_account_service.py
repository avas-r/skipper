from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from cryptography.fernet import Fernet
from datetime import datetime

from app.models import ServiceAccount, Agent, AgentSession, AgentLog
from app.schemas import ServiceAccountCreate, ServiceAccountUpdate, ServiceAccountResponse
from app.db.session import get_db
from app.auth.auth import get_current_active_user, verify_permissions

class EncryptionService:
    """Service for encrypting and decrypting sensitive data"""
    
    def __init__(self, key_provider):
        self.key_provider = key_provider
        
    def encrypt(self, data):
        """Encrypt data using the tenant's encryption key"""
        if isinstance(data, str):
            data = data.encode()
        
        # Get encryption key from provider
        key = self.key_provider.get_current_key()
        cipher = Fernet(key)
        
        # Encrypt and return as string
        encrypted = cipher.encrypt(data)
        return encrypted.decode()
        
    def decrypt(self, encrypted_data):
        """Decrypt data using the tenant's encryption key"""
        if isinstance(encrypted_data, str):
            encrypted_data = encrypted_data.encode()
        
        # Get encryption key from provider
        key = self.key_provider.get_current_key()
        cipher = Fernet(key)
        
        # Decrypt and return as string
        decrypted = cipher.decrypt(encrypted_data)
        return decrypted.decode()

class ServiceAccountService:
    """Service for managing robot service accounts"""
    
    def __init__(self, encryption_service=None):
        self.db = None
        self.encryption_service = encryption_service
        
    def set_db(self, db: Session):
        self.db = db
    
    def create_service_account(self, account: ServiceAccountCreate, tenant_id: uuid.UUID, 
                             user_id: uuid.UUID):
        """Create a new robot service account"""
        # Check if username already exists for tenant
        existing = self.db.query(ServiceAccount).filter(
            ServiceAccount.tenant_id == tenant_id,
            ServiceAccount.username == account.username
        ).first()
        
        if existing:
            raise ValueError(f"Service account with username '{account.username}' already exists")
        
        db_account = ServiceAccount(
            account_id=uuid.uuid4(),
            tenant_id=tenant_id,
            username=account.username,
            display_name=account.display_name,
            description=account.description,
            account_type=account.account_type,
            created_by=user_id,
            configuration={}
        )
        
        # Store password if provided (encrypted)
        if account.password and self.encryption_service:
            # Use the encryption service to secure the password
            encrypted_password = self.encryption_service.encrypt(account.password)
            db_account.configuration = {
                "credentials": {
                    "password": encrypted_password
                },
                "auto_login": account.auto_login_settings or {},
                "domain": account.domain,
                "creation_date": datetime.utcnow().isoformat()
            }
        elif account.password:
            # If no encryption service, store a placeholder
            db_account.configuration = {
                "credentials": {
                    "password": "PLACEHOLDER_NOT_STORED"
                },
                "auto_login": account.auto_login_settings or {},
                "domain": account.domain,
                "creation_date": datetime.utcnow().isoformat()
            }
        
        self.db.add(db_account)
        self.db.commit()
        self.db.refresh(db_account)
        
        # Log the creation
        self._log_service_account_action(
            db_account.account_id,
            tenant_id,
            user_id,
            "service_account_created",
            {"display_name": db_account.display_name}
        )
        
        return db_account
    
    def get_service_account(self, account_id: uuid.UUID, tenant_id: uuid.UUID, 
                          include_credentials: bool = False):
        """Get service account details"""
        account = self.db.query(ServiceAccount).filter(
            ServiceAccount.account_id == account_id,
            ServiceAccount.tenant_id == tenant_id
        ).first()
        
        if not account:
            return None
        
        # Create a copy to avoid modifying the database entity
        result = account.__dict__.copy()
        
        # Remove credentials if not explicitly requested
        if not include_credentials and "configuration" in result and result["configuration"]:
            if "credentials" in result["configuration"]:
                # Keep configuration but remove credentials
                config_copy = result["configuration"].copy()
                config_copy.pop("credentials", None)
                result["configuration"] = config_copy
                
        return result
    
    def list_service_accounts(self, tenant_id: uuid.UUID, 
                            search: Optional[str] = None,
                            account_type: Optional[str] = None,
                            status: Optional[str] = None,
                            skip: int = 0, limit: int = 100):
        """List service accounts with filtering options"""
        query = self.db.query(ServiceAccount).filter(
            ServiceAccount.tenant_id == tenant_id
        )
        
        if search:
            query = query.filter(
                (ServiceAccount.username.ilike(f"%{search}%")) |
                (ServiceAccount.display_name.ilike(f"%{search}%"))
            )
            
        if account_type:
            query = query.filter(ServiceAccount.account_type == account_type)
            
        if status:
            query = query.filter(ServiceAccount.status == status)
            
        total = query.count()
        
        accounts = query.order_by(ServiceAccount.created_at.desc()).offset(skip).limit(limit).all()
        
        # Remove credentials from all accounts
        for account in accounts:
            if account.configuration and "credentials" in account.configuration:
                account.configuration.pop("credentials", None)
                
        return {"total": total, "items": accounts}
    
    def update_service_account(self, account_id: uuid.UUID, account_update: ServiceAccountUpdate, 
                            tenant_id: uuid.UUID, user_id: uuid.UUID):
        """Update service account details"""
        db_account = self.db.query(ServiceAccount).filter(
            ServiceAccount.account_id == account_id,
            ServiceAccount.tenant_id == tenant_id
        ).first()
        
        if not db_account:
            return None
            
        # Update the fields that are provided
        update_data = account_update.dict(exclude_unset=True)
        
        # Special handling for password changes
        if "password" in update_data and update_data["password"] and self.encryption_service:
            # Get existing configuration
            configuration = db_account.configuration or {}
            
            if "credentials" not in configuration:
                configuration["credentials"] = {}
                
            # Update with encrypted password
            configuration["credentials"]["password"] = self.encryption_service.encrypt(
                update_data.pop("password")
            )
            configuration["password_updated_at"] = datetime.utcnow().isoformat()
            
            # Update configuration
            db_account.configuration = configuration
            
        # Update other fields
        for key, value in update_data.items():
            if key != "password" and key != "auto_login_settings" and hasattr(db_account, key):
                setattr(db_account, key, value)
                
        # Handle auto-login settings
        if "auto_login_settings" in update_data and update_data["auto_login_settings"]:
            configuration = db_account.configuration or {}
            configuration["auto_login"] = update_data["auto_login_settings"]
            db_account.configuration = configuration
            
        # Update timestamps
        db_account.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_account)
        
        # Log the update
        self._log_service_account_action(
            db_account.account_id,
            tenant_id,
            user_id,
            "service_account_updated",
            {"display_name": db_account.display_name}
        )
        
        return db_account
    
    def delete_service_account(self, account_id: uuid.UUID, tenant_id: uuid.UUID, user_id: uuid.UUID):
        """Delete a service account"""
        db_account = self.db.query(ServiceAccount).filter(
            ServiceAccount.account_id == account_id,
            ServiceAccount.tenant_id == tenant_id
        ).first()
        
        if not db_account:
            return False
            
        # Check if this account is used by any agents
        agent_count = self.db.query(Agent).filter(
            Agent.service_account_id == account_id
        ).count()
        
        if agent_count > 0:
            raise ValueError(f"Cannot delete service account that is used by {agent_count} agents")
            
        # Log before deletion
        display_name = db_account.display_name
        
        # Delete the account
        self.db.delete(db_account)
        self.db.commit()
        
        # Log the deletion
        self._log_service_account_action(
            account_id,
            tenant_id,
            user_id,
            "service_account_deleted",
            {"display_name": display_name}
        )
        
        return True
        
    def get_account_credentials(self, account_id: uuid.UUID, tenant_id: uuid.UUID, 
                              request_user_id: uuid.UUID = None):
        """Get decrypted service account credentials"""
        account = self.db.query(ServiceAccount).filter(
            ServiceAccount.account_id == account_id,
            ServiceAccount.tenant_id == tenant_id
        ).first()
        
        if not account or not account.configuration or "credentials" not in account.configuration:
            return None
            
        credentials = account.configuration.get("credentials", {})
        
        # Log access to credentials if user ID provided
        if request_user_id:
            self._log_service_account_action(
                account_id,
                tenant_id,
                request_user_id,
                "service_account_credentials_accessed",
                {"username": account.username}
            )
            
        # Decrypt password if present and encryption service is available
        if "password" in credentials and self.encryption_service:
            try:
                decrypted_password = self.encryption_service.decrypt(credentials["password"])
                return {
                    "username": account.username,
                    "password": decrypted_password,
                    "domain": account.configuration.get("domain"),
                    "auto_login": account.configuration.get("auto_login", {})
                }
            except Exception as e:
                # Log decryption error
                # In production, would log more details for debugging
                return None
        
        return None
    
    def _log_service_account_action(self, account_id, tenant_id, user_id, action, details=None):
        """Log service account actions to audit log"""
        # In a real implementation, this would log to an audit logging service
        # or to the database audit log table
        pass

class AgentSessionService:
    """Service for tracking agent sessions"""
    
    def __init__(self):
        self.db = None
        
    def set_db(self, db: Session):
        self.db = db
        
    def create_session(self, agent_id: uuid.UUID, tenant_id: uuid.UUID, 
                     service_account_id: Optional[uuid.UUID] = None,
                     status: str = "starting"):
        """Create a new agent session"""
        session = AgentSession(
            session_id=uuid.uuid4(),
            agent_id=agent_id,
            tenant_id=tenant_id,
            service_account_id=service_account_id,
            status=status,
            metadata={}
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        return session
        
    def update_session_status(self, session_id: uuid.UUID, status: str, metadata: dict = None):
        """Update an agent session status"""
        session = self.db.query(AgentSession).filter(
            AgentSession.session_id == session_id
        ).first()
        
        if not session:
            return None
            
        session.status = status
        session.last_updated_at = datetime.utcnow()
        
        if status in ["ended", "crashed", "terminated"]:
            session.ended_at = datetime.utcnow()
            
        if metadata:
            # Merge with existing metadata
            existing = session.metadata or {}
            existing.update(metadata)
            session.metadata = existing
            
        self.db.commit()
        self.db.refresh(session)
        
        return session
        
    def get_active_session(self, agent_id: uuid.UUID):
        """Get the active session for an agent"""
        return self.db.query(AgentSession).filter(
            AgentSession.agent_id == agent_id,
            AgentSession.ended_at.is_(None)
        ).order_by(AgentSession.started_at.desc()).first()
        
    def list_agent_sessions(self, agent_id: uuid.UUID, include_ended: bool = False, 
                          limit: int = 10):
        """List sessions for an agent"""
        query = self.db.query(AgentSession).filter(
            AgentSession.agent_id == agent_id
        )
        
        if not include_ended:
            query = query.filter(AgentSession.ended_at.is_(None))
            
        return query.order_by(AgentSession.started_at.desc()).limit(limit).all()
        
    def end_all_active_sessions(self, agent_id: uuid.UUID, status: str = "terminated"):
        """End all active sessions for an agent"""
        active_sessions = self.db.query(AgentSession).filter(
            AgentSession.agent_id == agent_id,
            AgentSession.ended_at.is_(None)
        ).all()
        
        for session in active_sessions:
            session.status = status
            session.ended_at = datetime.utcnow()
            session.last_updated_at = datetime.utcnow()
            
        self.db.commit()
        
        return len(active_sessions)