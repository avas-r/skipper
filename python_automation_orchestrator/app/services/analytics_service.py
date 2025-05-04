"""
Analytics service for data insights and statistics.

This module provides services for calculating analytics data, 
statistics, and trends for the orchestration system.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from calendar import monthrange
import uuid
from sqlalchemy import func, case, and_, extract, cast, Integer, Float, String
from sqlalchemy.sql import text
from sqlalchemy.orm import Session

from ..models import Job, JobExecution, Agent, User, Queue, QueueItem, Schedule

logger = logging.getLogger(__name__)

class AnalyticsService:
   """Service for analytics and statistics"""
   
   def __init__(self, db: Session):
       """Initialize with database session"""
       self.db = db
   
   def get_job_statistics(
       self,
       tenant_id: uuid.UUID,
       job_id: Optional[uuid.UUID] = None,
       start_date: Optional[datetime] = None,
       end_date: Optional[datetime] = None
   ) -> Dict[str, Any]:
       """Get job execution statistics"""
       query = self.db.query(JobExecution).filter(JobExecution.tenant_id == tenant_id)
       
       # Apply filters
       if job_id:
           query = query.filter(JobExecution.job_id == job_id)
       
       if start_date:
           query = query.filter(JobExecution.created_at >= start_date)
       
       if end_date:
           query = query.filter(JobExecution.created_at <= end_date)
       
       # Total executions
       total_executions = query.count()
       
       # Status breakdown
       status_counts = {}
       for status in ["completed", "failed", "cancelled", "running", "pending"]:
           count = query.filter(JobExecution.status == status).count()
           status_counts[status] = count
       
       # Success rate
       success_rate = 0
       total_completed = status_counts.get("completed", 0) + status_counts.get("failed", 0)
       if total_completed > 0:
           success_rate = round((status_counts.get("completed", 0) / total_completed) * 100, 2)
       
       # Average execution time
       avg_time = self.db.query(
           func.avg(JobExecution.execution_time_ms).label("avg_time")
       ).filter(
           JobExecution.tenant_id == tenant_id,
           JobExecution.status == "completed",
           JobExecution.execution_time_ms.isnot(None)
       )
       
       if job_id:
           avg_time = avg_time.filter(JobExecution.job_id == job_id)
       
       if start_date:
           avg_time = avg_time.filter(JobExecution.created_at >= start_date)
       
       if end_date:
           avg_time = avg_time.filter(JobExecution.created_at <= end_date)
       
       avg_execution_time = avg_time.scalar() or 0
       
       # Get most active jobs
       if not job_id:
           top_jobs_query = self.db.query(
               JobExecution.job_id,
               Job.name,
               func.count().label("execution_count")
           ).join(
               Job, JobExecution.job_id == Job.job_id
           ).filter(
               JobExecution.tenant_id == tenant_id
           )
           
           if start_date:
               top_jobs_query = top_jobs_query.filter(JobExecution.created_at >= start_date)
           
           if end_date:
               top_jobs_query = top_jobs_query.filter(JobExecution.created_at <= end_date)
           
           top_jobs = top_jobs_query.group_by(
               JobExecution.job_id, Job.name
           ).order_by(
               func.count().desc()
           ).limit(5).all()
           
           top_jobs_data = [
               {"job_id": str(job.job_id), "name": job.name, "execution_count": job.execution_count}
               for job in top_jobs
           ]
       else:
           top_jobs_data = []
       
       # Get failure trends
       failure_trend = self._get_job_failure_trend(
           tenant_id=tenant_id,
           job_id=job_id,
           start_date=start_date,
           end_date=end_date,
           interval="day"
       )
       
       return {
           "total_executions": total_executions,
           "status_counts": status_counts,
           "success_rate": success_rate,
           "avg_execution_time_ms": round(avg_execution_time, 2),
           "top_jobs": top_jobs_data,
           "failure_trend": failure_trend
       }
   
   def get_agent_statistics(
       self,
       tenant_id: uuid.UUID,
       agent_id: Optional[uuid.UUID] = None,
       start_date: Optional[datetime] = None,
       end_date: Optional[datetime] = None
   ) -> Dict[str, Any]:
       """Get agent statistics"""
       # Get agent query
       agent_query = self.db.query(Agent).filter(Agent.tenant_id == tenant_id)
       
       # Apply agent filter
       if agent_id:
           agent_query = agent_query.filter(Agent.agent_id == agent_id)
       
       # Get total agents and status breakdown
       total_agents = agent_query.count()
       
       agent_status = {}
       for status in ["online", "offline", "error"]:
           count = agent_query.filter(Agent.status == status).count()
           agent_status[status] = count
       
       # Get job execution statistics
       execution_query = self.db.query(JobExecution).filter(JobExecution.tenant_id == tenant_id)
       
       if agent_id:
           execution_query = execution_query.filter(JobExecution.agent_id == agent_id)
       
       if start_date:
           execution_query = execution_query.filter(JobExecution.created_at >= start_date)
       
       if end_date:
           execution_query = execution_query.filter(JobExecution.created_at <= end_date)
       
       # Total executions
       total_executions = execution_query.count()
       
       # Status breakdown
       execution_status = {}
       for status in ["completed", "failed", "cancelled"]:
           count = execution_query.filter(JobExecution.status == status).count()
           execution_status[status] = count
       
       # Success rate
       success_rate = 0
       total_completed = execution_status.get("completed", 0) + execution_status.get("failed", 0)
       if total_completed > 0:
           success_rate = round((execution_status.get("completed", 0) / total_completed) * 100, 2)
       
       # Average execution time
       avg_time = self.db.query(
           func.avg(JobExecution.execution_time_ms).label("avg_time")
       ).filter(
           JobExecution.tenant_id == tenant_id,
           JobExecution.status == "completed",
           JobExecution.execution_time_ms.isnot(None)
       )
       
       if agent_id:
           avg_time = avg_time.filter(JobExecution.agent_id == agent_id)
       
       if start_date:
           avg_time = avg_time.filter(JobExecution.created_at >= start_date)
       
       if end_date:
           avg_time = avg_time.filter(JobExecution.created_at <= end_date)
       
       avg_execution_time = avg_time.scalar() or 0
       
       # Get most active agents
       if not agent_id:
           top_agents_query = self.db.query(
               JobExecution.agent_id,
               Agent.name,
               func.count().label("execution_count")
           ).join(
               Agent, JobExecution.agent_id == Agent.agent_id
           ).filter(
               JobExecution.tenant_id == tenant_id
           )
           
           if start_date:
               top_agents_query = top_agents_query.filter(JobExecution.created_at >= start_date)
           
           if end_date:
               top_agents_query = top_agents_query.filter(JobExecution.created_at <= end_date)
           
           top_agents = top_agents_query.group_by(
               JobExecution.agent_id, Agent.name
           ).order_by(
               func.count().desc()
           ).limit(5).all()
           
           top_agents_data = [
               {"agent_id": str(agent.agent_id), "name": agent.name, "execution_count": agent.execution_count}
               for agent in top_agents
           ]
       else:
           top_agents_data = []
       
       # Get usage trend
       usage_trend = self._get_agent_usage_trend(
           tenant_id=tenant_id,
           agent_id=agent_id,
           start_date=start_date,
           end_date=end_date,
           interval="day"
       )
       
       return {
           "total_agents": total_agents,
           "agent_status": agent_status,
           "total_executions": total_executions,
           "execution_status": execution_status,
           "success_rate": success_rate,
           "avg_execution_time_ms": round(avg_execution_time, 2),
           "top_agents": top_agents_data,
           "usage_trend": usage_trend
       }
   
   def get_job_time_series(
       self,
       tenant_id: uuid.UUID,
       start_date: datetime,
       end_date: datetime,
       job_id: Optional[uuid.UUID] = None,
       interval: str = "day"
   ) -> List[Dict[str, Any]]:
       """Get job execution time series data"""
       # Determine date grouping based on interval
       if interval == "day":
           date_group = func.date_trunc('day', JobExecution.created_at)
           delta = timedelta(days=1)
       elif interval == "week":
           date_group = func.date_trunc('week', JobExecution.created_at)
           delta = timedelta(weeks=1)
       elif interval == "month":
           date_group = func.date_trunc('month', JobExecution.created_at)
           delta = timedelta(days=30)  # Approximation
       else:
           date_group = func.date_trunc('day', JobExecution.created_at)
           delta = timedelta(days=1)
       
       # Build query
       query = self.db.query(
           date_group.label('date'),
           func.count().label('total'),
           func.count(case([(JobExecution.status == 'completed', 1)])).label('completed'),
           func.count(case([(JobExecution.status == 'failed', 1)])).label('failed'),
           func.avg(JobExecution.execution_time_ms).label('avg_time')
       ).filter(
           JobExecution.tenant_id == tenant_id,
           JobExecution.created_at.between(start_date, end_date)
       )
       
       if job_id:
           query = query.filter(JobExecution.job_id == job_id)
       
       # Group and order
       query = query.group_by('date').order_by('date')
       
       # Execute query
       results = query.all()
       
       # Fill in missing dates
       data = []
       current_date = start_date
       
       results_dict = {result.date.date(): result for result in results}
       
       while current_date <= end_date:
           date_key = current_date.date()
           if date_key in results_dict:
               result = results_dict[date_key]
               data.append({
                   "date": date_key.isoformat(),
                   "total": result.total,
                   "completed": result.completed,
                   "failed": result.failed,
                   "avg_time_ms": round(result.avg_time or 0, 2)
               })
           else:
               data.append({
                   "date": date_key.isoformat(),
                   "total": 0,
                   "completed": 0,
                   "failed": 0,
                   "avg_time_ms": 0
               })
           
           # Increment date based on interval
           if interval == "day":
               current_date += timedelta(days=1)
           elif interval == "week":
               current_date += timedelta(weeks=1)
           elif interval == "month":
               # Move to first day of next month
               year = current_date.year + (current_date.month // 12)
               month = (current_date.month % 12) + 1
               current_date = datetime(year, month, 1)
       
       return data
   
   def get_dashboard_data(
       self,
       tenant_id: uuid.UUID,
       start_date: datetime,
       end_date: datetime
   ) -> Dict[str, Any]:
       """Get dashboard summary data"""
       # Get job statistics
       job_stats = self.get_job_statistics(
           tenant_id=tenant_id,
           start_date=start_date,
           end_date=end_date
       )
       
       # Get agent statistics
       agent_stats = self.get_agent_statistics(
           tenant_id=tenant_id,
           start_date=start_date,
           end_date=end_date
       )
       
       # Get recent activity
       recent_activity = self._get_recent_activity(tenant_id, limit=10)
       
       # Get pending items
       pending_items = self._get_pending_items(tenant_id)
       
       # Get upcoming scheduled jobs
       upcoming_jobs = self._get_upcoming_scheduled_jobs(tenant_id, limit=5)
       
       # Compile dashboard data
       return {
           "summary": {
               "total_executions": job_stats["total_executions"],
               "success_rate": job_stats["success_rate"],
               "avg_execution_time_ms": job_stats["avg_execution_time_ms"],
               "total_agents": agent_stats["total_agents"],
               "online_agents": agent_stats["agent_status"].get("online", 0),
               "pending_items": pending_items["total"]
           },
           "job_stats": job_stats,
           "agent_stats": agent_stats,
           "recent_activity": recent_activity,
           "pending_items": pending_items,
           "upcoming_jobs": upcoming_jobs
       }
   
   def get_top_jobs(
       self,
       tenant_id: uuid.UUID,
       start_date: datetime,
       end_date: datetime,
       limit: int = 10,
       metric: str = "executions"
   ) -> List[Dict[str, Any]]:
       """Get top jobs by various metrics"""
       # Build base query
       query = self.db.query(
           JobExecution.job_id,
           Job.name.label("job_name"),
           func.count().label("executions"),
           func.count(case([(JobExecution.status == 'completed', 1)])).label('successful'),
           func.count(case([(JobExecution.status == 'failed', 1)])).label('failed'),
           func.avg(JobExecution.execution_time_ms).label('avg_duration')
       ).join(
           Job, JobExecution.job_id == Job.job_id
       ).filter(
           JobExecution.tenant_id == tenant_id,
           JobExecution.created_at.between(start_date, end_date)
       ).group_by(
           JobExecution.job_id, Job.name
       )
       
       # Order by selected metric
       if metric == "executions":
           query = query.order_by(func.count().desc())
       elif metric == "failures":
           query = query.order_by(func.count(case([(JobExecution.status == 'failed', 1)])).desc())
       elif metric == "duration":
           query = query.order_by(func.avg(JobExecution.execution_time_ms).desc())
       
       # Limit results
       query = query.limit(limit)
       
       # Execute query
       results = query.all()
       
       # Format results
       return [
           {
               "job_id": str(result.job_id),
               "job_name": result.job_name,
               "executions": result.executions,
               "successful": result.successful,
               "failed": result.failed,
               "success_rate": round(result.successful / result.executions * 100, 2) if result.executions > 0 else 0,
               "avg_duration_ms": round(result.avg_duration or 0, 2)
           }
           for result in results
       ]
   
   def get_top_agents(
       self,
       tenant_id: uuid.UUID,
       start_date: datetime,
       end_date: datetime,
       limit: int = 10,
       metric: str = "executions"
   ) -> List[Dict[str, Any]]:
       """Get top agents by various metrics"""
       # Build base query
       query = self.db.query(
           JobExecution.agent_id,
           Agent.name.label("agent_name"),
           func.count().label("executions"),
           func.count(case([(JobExecution.status == 'completed', 1)])).label('successful'),
           func.count(case([(JobExecution.status == 'failed', 1)])).label('failed'),
           func.avg(JobExecution.execution_time_ms).label('avg_duration')
       ).join(
           Agent, JobExecution.agent_id == Agent.agent_id
       ).filter(
           JobExecution.tenant_id == tenant_id,
           JobExecution.created_at.between(start_date, end_date),
           JobExecution.agent_id.isnot(None)
       ).group_by(
           JobExecution.agent_id, Agent.name
       )
       
       # Order by selected metric
       if metric == "executions":
           query = query.order_by(func.count().desc())
       elif metric == "failures":
           query = query.order_by(func.count(case([(JobExecution.status == 'failed', 1)])).desc())
       elif metric == "duration":
           query = query.order_by(func.avg(JobExecution.execution_time_ms).desc())
       
       # Limit results
       query = query.limit(limit)
       
       # Execute query
       results = query.all()
       
       # Format results
       return [
           {
               "agent_id": str(result.agent_id),
               "agent_name": result.agent_name,
               "executions": result.executions,
               "successful": result.successful,
               "failed": result.failed,
               "success_rate": round(result.successful / result.executions * 100, 2) if result.executions > 0 else 0,
               "avg_duration_ms": round(result.avg_duration or 0, 2)
           }
           for result in results
       ]
   
   def _get_job_failure_trend(
       self,
       tenant_id: uuid.UUID,
       start_date: Optional[datetime],
       end_date: Optional[datetime],
       job_id: Optional[uuid.UUID] = None,
       interval: str = "day"
   ) -> List[Dict[str, Any]]:
       """Get job failure trend data"""
       # Set default dates if not provided
       if not end_date:
           end_date = datetime.utcnow()
       
       if not start_date:
           start_date = end_date - timedelta(days=30)
       
       # Determine date grouping based on interval
       if interval == "day":
           date_group = func.date_trunc('day', JobExecution.created_at)
       elif interval == "week":
           date_group = func.date_trunc('week', JobExecution.created_at)
       elif interval == "month":
           date_group = func.date_trunc('month', JobExecution.created_at)
       else:
           date_group = func.date_trunc('day', JobExecution.created_at)
       
       # Build query
       query = self.db.query(
           date_group.label('date'),
           func.count().label('total'),
           func.count(case([(JobExecution.status == 'failed', 1)])).label('failed')
       ).filter(
           JobExecution.tenant_id == tenant_id,
           JobExecution.created_at.between(start_date, end_date)
       )
       
       if job_id:
           query = query.filter(JobExecution.job_id == job_id)
       
       # Group and order
       query = query.group_by('date').order_by('date')
       
       # Execute query
       results = query.all()
       
       # Calculate failure rates
       return [
           {
               "date": result.date.strftime("%Y-%m-%d"),
               "failure_rate": round(result.failed / result.total * 100, 2) if result.total > 0 else 0
           }
           for result in results
       ]
   
   def _get_agent_usage_trend(
       self,
       tenant_id: uuid.UUID,
       start_date: Optional[datetime],
       end_date: Optional[datetime],
       agent_id: Optional[uuid.UUID] = None,
       interval: str = "day"
   ) -> List[Dict[str, Any]]:
       """Get agent usage trend data"""
       # Set default dates if not provided
       if not end_date:
           end_date = datetime.utcnow()
       
       if not start_date:
           start_date = end_date - timedelta(days=30)
       
       # Determine date grouping based on interval
       if interval == "day":
           date_group = func.date_trunc('day', JobExecution.created_at)
       elif interval == "week":
           date_group = func.date_trunc('week', JobExecution.created_at)
       elif interval == "month":
           date_group = func.date_trunc('month', JobExecution.created_at)
       else:
           date_group = func.date_trunc('day', JobExecution.created_at)
       
       # Build query
       query = self.db.query(
           date_group.label('date'),
           func.count().label('executions'),
           func.avg(JobExecution.execution_time_ms).label('avg_time')
       ).filter(
           JobExecution.tenant_id == tenant_id,
           JobExecution.created_at.between(start_date, end_date),
           JobExecution.agent_id.isnot(None)
       )
       
       if agent_id:
           query = query.filter(JobExecution.agent_id == agent_id)
       
       # Group and order
       query = query.group_by('date').order_by('date')
       
       # Execute query
       results = query.all()
       
       # Format results
       return [
           {
               "date": result.date.strftime("%Y-%m-%d"),
               "executions": result.executions,
               "avg_time_ms": round(result.avg_time or 0, 2)
           }
           for result in results
       ]
   
   def _get_recent_activity(self, tenant_id: uuid.UUID, limit: int = 10) -> List[Dict[str, Any]]:
       """Get recent activity (job executions)"""
       # Get recent job executions
       executions = self.db.query(
           JobExecution.execution_id,
           JobExecution.job_id,
           Job.name.label("job_name"),
           JobExecution.status,
           JobExecution.agent_id,
           Agent.name.label("agent_name"),
           JobExecution.created_at,
           JobExecution.completed_at,
           JobExecution.execution_time_ms
       ).join(
           Job, JobExecution.job_id == Job.job_id
       ).outerjoin(
           Agent, JobExecution.agent_id == Agent.agent_id
       ).filter(
           JobExecution.tenant_id == tenant_id
       ).order_by(
           JobExecution.created_at.desc()
       ).limit(limit).all()
       
       # Format results
       return [
           {
               "type": "job_execution",
               "execution_id": str(execution.execution_id),
               "job_id": str(execution.job_id),
               "job_name": execution.job_name,
               "status": execution.status,
               "agent_id": str(execution.agent_id) if execution.agent_id else None,
               "agent_name": execution.agent_name,
               "created_at": execution.created_at.isoformat(),
               "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
               "execution_time_ms": execution.execution_time_ms
           }
           for execution in executions
       ]
   
   def _get_pending_items(self, tenant_id: uuid.UUID) -> Dict[str, Any]:
       """Get pending queue items"""
       # Get total pending items
       total_pending = self.db.query(func.count(QueueItem.item_id)).filter(
           QueueItem.tenant_id == tenant_id,
           QueueItem.status == "pending"
       ).scalar() or 0
       
       # Get pending items by queue
       queue_items = self.db.query(
           Queue.queue_id,
           Queue.name,
           func.count(QueueItem.item_id).label("pending_count")
       ).join(
           QueueItem, Queue.queue_id == QueueItem.queue_id
       ).filter(
           Queue.tenant_id == tenant_id,
           QueueItem.status == "pending"
       ).group_by(
           Queue.queue_id, Queue.name
       ).order_by(
           func.count(QueueItem.item_id).desc()
       ).all()
       
       # Format results
       return {
           "total": total_pending,
           "queues": [
               {
                   "queue_id": str(item.queue_id),
                   "queue_name": item.name,
                   "pending_count": item.pending_count
               }
               for item in queue_items
           ]
       }
   
   def _get_upcoming_scheduled_jobs(self, tenant_id: uuid.UUID, limit: int = 5) -> List[Dict[str, Any]]:
       """Get upcoming scheduled jobs"""
       # Get schedules with next execution time
       schedules = self.db.query(
           Schedule.schedule_id,
           Schedule.name.label("schedule_name"),
           Schedule.next_execution,
           func.count(Job.job_id).label("job_count")
       ).join(
           Job, Schedule.schedule_id == Job.schedule_id
       ).filter(
           Schedule.tenant_id == tenant_id,
           Schedule.status == "active",
           Job.status == "active",
           Schedule.next_execution.isnot(None)
       ).group_by(
           Schedule.schedule_id, Schedule.name, Schedule.next_execution
       ).order_by(
           Schedule.next_execution
       ).limit(limit).all()
       
       # Format results
       return [
           {
               "schedule_id": str(schedule.schedule_id),
               "schedule_name": schedule.schedule_name,
               "next_execution": schedule.next_execution.isoformat(),
               "job_count": schedule.job_count
           }
           for schedule in schedules
       ]