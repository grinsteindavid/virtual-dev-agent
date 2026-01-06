"""LangChain tools for Virtual Developer Agent."""

from src.tools.github import GITHUB_TOOLS
from src.tools.jira import JIRA_TOOLS
from src.tools.discord import DISCORD_TOOLS
from src.tools.filesystem import FILESYSTEM_TOOLS
from src.tools.git import GIT_TOOLS

ALL_TOOLS = GITHUB_TOOLS + JIRA_TOOLS + DISCORD_TOOLS + FILESYSTEM_TOOLS + GIT_TOOLS

__all__ = [
    "GITHUB_TOOLS",
    "JIRA_TOOLS",
    "DISCORD_TOOLS",
    "FILESYSTEM_TOOLS",
    "GIT_TOOLS",
    "ALL_TOOLS",
]
