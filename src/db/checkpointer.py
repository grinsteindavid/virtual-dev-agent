"""Redis checkpointer for LangGraph state persistence."""

from typing import Optional

from langgraph.checkpoint.base import BaseCheckpointSaver

from src.config import config
from src.logger import get_logger

logger = get_logger(__name__)

_checkpointer: Optional[BaseCheckpointSaver] = None


def get_checkpointer() -> Optional[BaseCheckpointSaver]:
    """Get or create the Redis checkpointer singleton.
    
    Returns None if Redis is not configured or unavailable.
    """
    global _checkpointer
    
    if _checkpointer is not None:
        return _checkpointer
    
    if not config.redis.is_valid:
        logger.warning("Redis not configured, checkpointing disabled")
        return None
    
    try:
        from langgraph.checkpoint.memory import MemorySaver
        _checkpointer = MemorySaver()
        logger.info("Using memory saver for checkpointing")
        return _checkpointer
        
    except Exception as e:
        logger.warning(f"Failed to create checkpointer: {e}")
        return None


def reset_checkpointer() -> None:
    """Reset the checkpointer singleton (for testing)."""
    global _checkpointer
    _checkpointer = None
