"""
Analytics endpoints for the orchestrator API.

This module provides endpoints for data analytics and statistics.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session
import uuid

from ....auth.jwt import get_current_active_user
from ....auth.permissions import PermissionChecker
from ....db.session import get_db
from ....models import User, Job, JobExecution, Agent
from ....services.analytics_service import AnalyticsService

router = APIRouter()
logger = logging.getLogger(__name__)

# Permission dependencies
require_analytics_read = PermissionChecker(["analytics:read"])

@router.get("/job-stats")
async def get_job_statistics(
   start_date: Optional[datetime] = Query(None),
   end_date: Optional[datetime] = Query(None),
   job_id: Optional[uuid.UUID] = None,
   db: Session = Depends(get_db),
   current_user: User = Depends(get_current_active_user),
   _: bool = Depends(require_analytics_read)
) -> Dict[str, Any]:
   """
   Get job execution statistics.
   
   If no dates provided, defaults to last 7 days.
   """
   # Set default date range if not provided
   if not end_date:
       end_date = datetime.utcnow()
   
   if not start_date:
       start_date = end_date - timedelta(days=7)
   
   # Create analytics service
   analytics_service = AnalyticsService(db)
   
   # Get statistics
   stats = analytics_service.get_job_statistics(
       tenant_id=current_user.tenant_id,
       job_id=job_id,
       start_date=start_date,
       end_date=end_date
   )
   
   return stats

@router.get("/agent-stats")
async def get_agent_statistics(
   start_date: Optional[datetime] = Query(None),
   end_date: Optional[datetime] = Query(None),
   agent_id: Optional[uuid.UUID] = None,
   db: Session = Depends(get_db),
   current_user: User = Depends(get_current_active_user),
   _: bool = Depends(require_analytics_read)
) -> Dict[str, Any]:
   """
   Get agent statistics.
   
   If no dates provided, defaults to last 7 days.
   """
   # Set default date range if not provided
   if not end_date:
       end_date = datetime.utcnow()
   
   if not start_date:
       start_date = end_date - timedelta(days=7)
   
   # Create analytics service
   analytics_service = AnalyticsService(db)
   
   # Get statistics
   stats = analytics_service.get_agent_statistics(
       tenant_id=current_user.tenant_id,
       agent_id=agent_id,
       start_date=start_date,
       end_date=end_date
   )
   
   return stats

@router.get("/time-series/jobs")
async def get_job_time_series(
   start_date: Optional[datetime] = Query(None),
   end_date: Optional[datetime] = Query(None),
   job_id: Optional[uuid.UUID] = None,
   interval: str = Query("day", description="Aggregation interval: day, week, month"),
   db: Session = Depends(get_db),
   current_user: User = Depends(get_current_active_user),
   _: bool = Depends(require_analytics_read)
) -> List[Dict[str, Any]]:
   """
   Get job execution time series data.
   
   If no dates provided, defaults to last 30 days.
   """
   # Set default date range if not provided
   if not end_date:
       end_date = datetime.utcnow()
   
   if not start_date:
       start_date = end_date - timedelta(days=30)
   
   # Validate interval
   valid_intervals = ["day", "week", "month"]
   if interval not in valid_intervals:
       raise HTTPException(
           status_code=status.HTTP_400_BAD_REQUEST,
           detail=f"Invalid interval. Must be one of: {', '.join(valid_intervals)}"
       )
   
   # Create analytics service
   analytics_service = AnalyticsService(db)
   
   # Get time series data
   data = analytics_service.get_job_time_series(
       tenant_id=current_user.tenant_id,
       job_id=job_id,
       start_date=start_date,
       end_date=end_date,
       interval=interval
   )
   
   return data

@router.get("/dashboard")
async def get_dashboard_data(
   days: int = Query(30, description="Number of days to include in trends"),
   db: Session = Depends(get_db),
   current_user: User = Depends(get_current_active_user),
   _: bool = Depends(require_analytics_read)
) -> Dict[str, Any]:
   """
   Get dashboard summary data.
   """
   # Calculate date range
   end_date = datetime.utcnow()
   start_date = end_date - timedelta(days=days)
   
   # Create analytics service
   analytics_service = AnalyticsService(db)
   
   # Get dashboard data
   dashboard = analytics_service.get_dashboard_data(
       tenant_id=current_user.tenant_id,
       start_date=start_date,
       end_date=end_date
   )
   
   return dashboard

@router.get("/top/jobs")
async def get_top_jobs(
   start_date: Optional[datetime] = Query(None),
   end_date: Optional[datetime] = Query(None),
   limit: int = Query(10, description="Number of jobs to return"),
   metric: str = Query("executions", description="Ranking metric: executions, failures, duration"),
   db: Session = Depends(get_db),
   current_user: User = Depends(get_current_active_user),
   _: bool = Depends(require_analytics_read)
) -> List[Dict[str, Any]]:
   """
   Get top jobs by various metrics.
   """
   # Set default date range if not provided
   if not end_date:
       end_date = datetime.utcnow()
   
   if not start_date:
       start_date = end_date - timedelta(days=30)
   
   # Validate metric
   valid_metrics = ["executions", "failures", "duration"]
   if metric not in valid_metrics:
       raise HTTPException(
           status_code=status.HTTP_400_BAD_REQUEST,
           detail=f"Invalid metric. Must be one of: {', '.join(valid_metrics)}"
       )
   
   # Create analytics service
   analytics_service = AnalyticsService(db)
   
   # Get top jobs
   jobs = analytics_service.get_top_jobs(
       tenant_id=current_user.tenant_id,
       start_date=start_date,
       end_date=end_date,
       limit=limit,
       metric=metric
   )
   
   return jobs

@router.get("/top/agents")
async def get_top_agents(
   start_date: Optional[datetime] = Query(None),
   end_date: Optional[datetime] = Query(None),
   limit: int = Query(10, description="Number of agents to return"),
   metric: str = Query("executions", description="Ranking metric: executions, failures, duration"),
   db: Session = Depends(get_db),
   current_user: User = Depends(get_current_active_user),
   _: bool = Depends(require_analytics_read)
) -> List[Dict[str, Any]]:
   """
   Get top agents by various metrics.
   """
   # Set default date range if not provided
   if not end_date:
       end_date = datetime.utcnow()
   
   if not start_date:
       start_date = end_date - timedelta(days=30)
   
   # Validate metric
   valid_metrics = ["executions", "failures", "duration"]
   if metric not in valid_metrics:
       raise HTTPException(
           status_code=status.HTTP_400_BAD_REQUEST,
           detail=f"Invalid metric. Must be one of: {', '.join(valid_metrics)}"
       )
   
   # Create analytics service
   analytics_service = AnalyticsService(db)
   
   # Get top agents
   agents = analytics_service.get_top_agents(
       tenant_id=current_user.tenant_id,
       start_date=start_date,
       end_date=end_date,
       limit=limit,
       metric=metric
   )
   
   return agents