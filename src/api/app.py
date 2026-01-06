"""FastAPI application factory."""

from fastapi import FastAPI

from src import __version__
from src.api.routes import health, tasks


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Virtual Developer Agent",
        description="LangGraph-based virtual developer for automated Jira-to-PR workflow",
        version=__version__,
    )
    
    app.include_router(health.router)
    app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
    
    return app
