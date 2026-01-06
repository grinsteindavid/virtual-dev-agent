"""Prompt templates for agents."""

from src.agents.prompts.implementer import IMPLEMENTATION_PROMPT, COMPLETION_CHECK_PROMPT
from src.agents.prompts.planner import PLANNING_PROMPT
from src.agents.prompts.supervisor import ROUTING_PROMPT
from src.agents.prompts.tester import FIX_PROMPT

__all__ = [
    "IMPLEMENTATION_PROMPT",
    "COMPLETION_CHECK_PROMPT",
    "PLANNING_PROMPT",
    "ROUTING_PROMPT",
    "FIX_PROMPT",
]
