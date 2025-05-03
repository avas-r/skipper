"""
Job model for automation job management.

This module defines the Job, JobExecution, and JobDependency models
for managing automation jobs and their execution.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Text, Integer, JSON, ForeignKey, UniqueConstraint, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from ..db.session import Base

class Job(Base):
    """
    Job model for automation job management.
    
    Jobs represent automation tasks that can be executed manually or
    according to schedules.
    """
    
    __tablename__ = "jobs"
    
    # Primary key
    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant foreign key
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    tenant = relationship("Tenant", backref="jobs")
    
    # Package foreign key
    package_id = Column(UUID(as_uuid=True), ForeignKey("packages.package_id"), nullable=False)
    package = relationship("Package", back_populates="jobs")
    
    # Schedule foreign key (optional)
    schedule_id = Column(UUID(as_uuid=True), ForeignKey("schedules.schedule_id"), nullable=True)
    schedule = relationship("Schedule", back_populates="jobs")
    
    # Queue foreign key (optional)
    queue_id = Column(UUID(as_uuid=True), ForeignKey("queues.queue_id"), nullable=True)
    queue = relationship("Queue", back_populates="jobs")
    
    # Job information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Job configuration
    priority = Column(Integer, nullable=False, default=1)
    max_concurrent_runs = Column(Integer, nullable=False, default=1)
    timeout_seconds = Column(Integer, nullable=False, default=3600)
    retry_count = Column(Integer, nullable=False, default=0)
    retry_delay_seconds = Column(Integer, nullable=False, default=60)
    
    # Job parameters
    parameters = Column(JSON, nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default="active")
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    executions = relationship("JobExecution", back_populates="job", cascade="all, delete-orphan")
    
    # Dependencies
    dependencies = relationship(
        "Job",
        secondary="job_dependencies",
        primaryjoin="Job.job_id == JobDependency.job_id",
        secondaryjoin="Job.job_id == JobDependency.depends_on_job_id",
        backref="dependent_jobs"
    )
    
    # Unique constraint for tenant + name
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_job_tenant_name"),
    )
    
    def __repr__(self):
        """String representation of the job"""
        return f"<Job {self.name} ({self.job_id})>"

class JobExecution(Base):
    """
    Job execution model.
    
    Job executions represent individual runs of a job.
    """
    
    __tablename__ = "job_executions"
    
    # Primary key
    execution_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Job foreign key
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.job_id"), nullable=False)
    job = relationship("Job", back_populates="executions")
    
    # Tenant foreign key
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    tenant = relationship("Tenant")
    
    # Agent foreign key (optional)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.agent_id"), nullable=True)
    agent = relationship("Agent", back_populates="job_executions")
    
    # Queue item foreign key (optional)
    queue_item_id = Column(UUID(as_uuid=True), ForeignKey("queue_items.item_id"), nullable=True)
    queue_item = relationship("QueueItem", back_populates="job_executions")
    
    # Execution information
    status = Column(String(20), nullable=False, default="pending")
    trigger_type = Column(String(50), nullable=False)  # "manual", "scheduled", "dependency", etc.
    
    # Execution timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    
    # Execution data
    input_parameters = Column(JSON, nullable=True)
    output_results = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Storage paths for logs, screenshots, and recordings
    logs_path = Column(String(255), nullable=True)
    screenshots_path = Column(String(255), nullable=True)
    recording_path = Column(String(255), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        """String representation of the job execution"""
        return f"<JobExecution {self.execution_id} - {self.status}>"

class JobDependency(Base):
    """
    Job dependency model.
    
    Defines dependencies between jobs, where one job depends on the completion
    of another job.
    """
    
    __tablename__ = "job_dependencies"
    
    # Composite primary key
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.job_id"), primary_key=True)
    depends_on_job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.job_id"), primary_key=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    def __repr__(self):
        """String representation of the job dependency"""
        return f"<JobDependency {self.job_id} -> {self.depends_on_job_id}>"