"""
Agent package endpoints for the orchestrator API.

This module provides endpoints for agents to interact with packages:
- Get packages assigned to the agent
- Report package execution status
- Upload packaged results
"""

import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ....auth.jwt import get_current_active_user, get_current_agent
from ....db.session import get_db
from ....models import User, Agent, Package, Job, JobExecution
from ....services.package_service import PackageService
from ....services.job_service import JobService
from ....schemas.package import PackageStatusUpdate, PackageExecuteRequest

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/agent-packages")
def list_agent_packages(
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
) -> Any:
    """
    List packages available for this agent.
    
    This endpoint is used by agents to retrieve packages assigned to them.
    """
    # Create package service
    package_service = PackageService(db)
    
    # List packages
    packages = package_service.list_packages_for_agent(
        agent_id=str(current_agent.agent_id),
        tenant_id=str(current_agent.tenant_id)
    )
    
    return {
        "packages": packages
    }

@router.post("/execute-package")
def agent_execute_package(
    execute_request: PackageExecuteRequest,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent),
    background_tasks: BackgroundTasks = None
) -> Dict[str, Any]:
    """
    Request to execute a package on an agent.
    
    This endpoint is used by agents to report when they need to execute a package.
    """
    # Create job service
    job_service = JobService(db)
    
    # Create execution record
    execution = job_service.create_package_execution(
        agent_id=str(current_agent.agent_id),
        tenant_id=str(current_agent.tenant_id),
        package_id=execute_request.package_id,
        parameters=execute_request.parameters
    )
    
    # Return execution ID
    return {
        "execution_id": execution.execution_id,
        "status": "queued"
    }

@router.post("/execution/{execution_id}/status")
def update_execution_status(
    execution_id: str,
    status_update: PackageStatusUpdate,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
) -> Dict[str, Any]:
    """
    Update package execution status.
    
    This endpoint is used by agents to report package execution status.
    """
    # Create job service
    job_service = JobService(db)
    
    # Update execution status
    execution = job_service.update_execution_status(
        execution_id=execution_id,
        agent_id=str(current_agent.agent_id),
        tenant_id=str(current_agent.tenant_id),
        status=status_update.status,
        progress=status_update.progress,
        results=status_update.results,
        error=status_update.error
    )
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found"
        )
    
    return {
        "execution_id": execution_id,
        "status": execution.status
    }

@router.post("/execution/{execution_id}/upload")
def upload_execution_result(
    execution_id: str,
    file: UploadFile = File(...),
    result_type: str = Form(...),
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
) -> Dict[str, Any]:
    """
    Upload package execution result file.
    
    This endpoint is used by agents to upload files produced during package execution.
    """
    # Create job service
    job_service = JobService(db)
    
    # Check if execution exists
    execution = job_service.get_execution(
        execution_id=execution_id,
        tenant_id=str(current_agent.tenant_id)
    )
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found"
        )
    
    # Check if agent is allowed to upload for this execution
    if str(execution.agent_id) != str(current_agent.agent_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to upload for this execution"
        )
    
    try:
        # Save the file
        result_path = job_service.save_execution_result(
            execution_id=execution_id,
            file=file,
            result_type=result_type
        )
        
        return {
            "execution_id": execution_id,
            "result_type": result_type,
            "file_path": result_path
        }
    except Exception as e:
        logger.error(f"Error saving execution result: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving execution result: {str(e)}"
        )

@router.post("/upload-package")
def agent_upload_package(
    file: UploadFile = File(...),
    name: str = Form(...),
    version: str = Form(...),
    description: Optional[str] = Form(None),
    entry_point: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
) -> Dict[str, Any]:
    """
    Upload a package from an agent.
    
    This endpoint allows agents to upload packages they've created or modified.
    """
    # Create package service
    package_service = PackageService(db)
    
    # Process and save the uploaded package
    try:
        package = package_service.process_agent_package_upload(
            file=file,
            name=name,
            version=version,
            description=description,
            entry_point=entry_point,
            tenant_id=str(current_agent.tenant_id),
            agent_id=str(current_agent.agent_id)
        )
        
        return {
            "package_id": str(package.package_id),
            "name": package.name,
            "version": package.version,
            "status": "uploaded"
        }
    except Exception as e:
        logger.error(f"Error processing agent package upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing package upload: {str(e)}"
        )