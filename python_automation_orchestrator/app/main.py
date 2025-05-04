"""
Main application module for the Python Automation Orchestrator.

This module initializes the FastAPI application, configures middleware,
sets up routes, and initializes core services.
"""

import logging
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .api.api_v1.api import api_router
from .db.session import engine, SessionLocal
from .db.base import Base
from .messaging.producer import get_message_producer
from .utils.logging import setup_logging

# Set up logging
logger = setup_logging()

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        docs_url=None,  # Custom docs URL below
        openapi_url=None,  # Custom OpenAPI URL below
        redoc_url=None,  # Disable ReDoc
    )
    
    # Configure CORS
    if settings.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # Mount static files
    #app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Custom OpenAPI schema
    @app.get("/openapi.json", include_in_schema=False)
    async def get_open_api_schema():
        return get_openapi(
            title=settings.APP_NAME,
            version=settings.APP_VERSION,
            description=settings.APP_DESCRIPTION,
            routes=app.routes,
        )
    
    # Custom Swagger UI
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title=f"{settings.APP_NAME} - API Documentation",
            swagger_js_url="/static/swagger-ui-bundle.js",
            swagger_css_url="/static/swagger-ui.css",
        )
    
    # Exception handlers
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler for the application"""
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred. Please try again later."},
        )
    
    # Startup and shutdown events
    @app.on_event("startup")
    async def startup_event():
        """Application startup event handler"""
        logger.info(f"Starting {settings.APP_NAME} version {settings.APP_VERSION}")
        logger.info(f"Environment: {settings.ENVIRONMENT}")
        logger.info("Creating database tables if they don't exist")
        Base.metadata.create_all(bind=engine)
        
        # Initialize message producer
        producer = get_message_producer()
        await producer.connect()
        
        # Start background tasks
        from .workers import start_workers
        start_workers()
        
        logger.info("Application startup complete")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Application shutdown event handler"""
        logger.info("Shutting down application")
        
        # Stop background tasks
        from .workers import stop_workers
        await stop_workers()
        
        # Close message producer
        producer = get_message_producer()
        await producer.close()
        
        logger.info("Application shutdown complete")
    
    # Request lifecycle events
    @app.middleware("http")
    async def db_session_middleware(request: Request, call_next):
        """Middleware to handle database session per request"""
        response = None
        try:
            # Create database session for each request
            request.state.db = SessionLocal()
            response = await call_next(request)
        finally:
            # Close database session after request
            if hasattr(request.state, "db"):
                request.state.db.close()
        return response
    
    # API routers
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "version": settings.APP_VERSION}
    
    return app

# Create application instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )