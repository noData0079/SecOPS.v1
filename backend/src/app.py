"""
SecOps-AI FastAPI Application

Production-ready API for security operations automation.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.v1.endpoints import (
    findings_router,
    playbooks_router,
    system_router,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("SecOps-AI starting up...")
    # Initialize services here (database, vector store, etc.)
    yield
    logger.info("SecOps-AI shutting down...")
    # Cleanup here


# Create FastAPI app
app = FastAPI(
    title="SecOps-AI",
    description="Agentic AI Platform for Security Operations",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(findings_router, prefix="/api/v1")
app.include_router(playbooks_router, prefix="/api/v1")
app.include_router(system_router, prefix="/api/v1")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "SecOps-AI",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "api": "/api/v1",
    }


# Health check at root level
@app.get("/health")
async def health():
    """Simple health check."""
    return {"status": "ok"}


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
