"""
Logging utility module.

This module provides logging configuration and utilities for 
the orchestration system.
"""

import logging
import sys
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from ..config import settings

class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    
    Formats log records as JSON for easier parsing and analysis.
    """
    
    def format(self, record):
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            str: Formatted log record as JSON
        """
        # Get basic log record attributes
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        
        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        # Add record attributes
        for key, value in record.__dict__.items():
            if key not in ("args", "asctime", "created", "exc_info", "exc_text", 
                         "filename", "funcName", "id", "levelname", "levelno",
                         "lineno", "module", "msecs", "message", "msg", "name", 
                         "pathname", "process", "processName", "relativeCreated", 
                         "stack_info", "thread", "threadName"):
                log_data[key] = value
                
        # Convert to JSON
        return json.dumps(log_data)

def setup_logging():
    """
    Set up logging configuration.
    
    Returns:
        logging.Logger: Configured logger
    """
    # Get log level from settings
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger("orchestrator")
    logger.setLevel(log_level)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(settings.LOG_FORMAT)
    console_handler.setFormatter(formatter)
    
    # Add console handler to logger
    logger.addHandler(console_handler)
    
    # Add file handler if log file is specified
    if settings.LOG_FILE:
        # Create logs directory if it doesn't exist
        log_path = Path(settings.LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create file handler with rotation
        file_handler = RotatingFileHandler(
            settings.LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        
        # Use JSON formatter for file logs
        json_formatter = JSONFormatter()
        file_handler.setFormatter(json_formatter)
        
        # Add file handler to logger
        logger.addHandler(file_handler)
    
    # Set up additional loggers for dependencies
    for module_name in ["sqlalchemy.engine", "aio_pika", "fastapi"]:
        module_logger = logging.getLogger(module_name)
        module_logger.setLevel(log_level)
        module_logger.handlers = []  # Remove existing handlers
        module_logger.addHandler(console_handler)
        
        if settings.LOG_FILE:
            module_logger.addHandler(file_handler)
    
    logger.info(f"Logging initialized at level {settings.LOG_LEVEL}")
    
    return logger


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter for adding context to log records.
    
    Adds tenant, user, request, and other context information to log records.
    """
    
    def __init__(self, logger, extra=None):
        """
        Initialize the logger adapter.
        
        Args:
            logger: Base logger
            extra: Extra context information
        """
        super().__init__(logger, extra or {})
    
    def process(self, msg, kwargs):
        """
        Process the log record by adding context information.
        
        Args:
            msg: Log message
            kwargs: Additional keyword arguments
            
        Returns:
            tuple: Processed message and keyword arguments
        """
        # Add extra context to kwargs
        if "extra" not in kwargs:
            kwargs["extra"] = {}
            
        kwargs["extra"].update(self.extra)
        
        return msg, kwargs


def get_logger(name, **context):
    """
    Get a logger with context.
    
    Args:
        name: Logger name
        **context: Additional context information
        
    Returns:
        LoggerAdapter: Logger adapter with context
    """
    logger = logging.getLogger(name)
    return LoggerAdapter(logger, context)


def log_request(request, logger=None):
    """
    Log incoming HTTP request.
    
    Args:
        request: FastAPI request object
        logger: Logger to use (if None, use default logger)
        
    Returns:
        dict: Request information
    """
    logger = logger or logging.getLogger("orchestrator.api")
    
    # Extract request information
    request_info = {
        "method": request.method,
        "url": str(request.url),
        "client": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }
    
    # Add authorization header (without token)
    if "authorization" in request.headers:
        auth_header = request.headers["authorization"]
        if auth_header.lower().startswith("bearer "):
            request_info["auth"] = "Bearer [redacted]"
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}", extra={"request": request_info})
    
    return request_info


def log_response(response, request_time, logger=None):
    """
    Log HTTP response.
    
    Args:
        response: FastAPI response object
        request_time: Request processing time in seconds
        logger: Logger to use (if None, use default logger)
        
    Returns:
        dict: Response information
    """
    logger = logger or logging.getLogger("orchestrator.api")
    
    # Extract response information
    response_info = {
        "status_code": response.status_code,
        "processing_time": round(request_time * 1000, 2),  # ms
    }
    
    # Log response
    log_level = logging.INFO if response.status_code < 400 else logging.WARNING
    logger.log(
        log_level, 
        f"Response: {response.status_code} in {response_info['processing_time']}ms",
        extra={"response": response_info}
    )
    
    return response_info