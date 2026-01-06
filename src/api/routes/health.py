"""Health check endpoint."""

from fastapi import APIRouter

from src import __version__
from src.config import config

router = APIRouter()


@router.get("/health")
def health_check():
    """Return health status of the service."""
    errors = config.validate()
    return {
        "status": "ok" if not errors else "degraded",
        "version": __version__,
        "config_errors": errors if errors else None,
    }
