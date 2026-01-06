"""Jira LangChain tools."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.clients.jira_client import get_jira_client
from src.logger import get_logger

logger = get_logger(__name__)


class GetJiraIssueInput(BaseModel):
    """Input for get_jira_issue tool."""
    issue_key: str = Field(description="The Jira issue key (e.g., DP-4)")


class ListJiraIssuesInput(BaseModel):
    """Input for list_jira_issues tool."""
    status: str = Field(default="To Do", description="Filter by status")
    limit: int = Field(default=10, description="Maximum results")


class AddJiraCommentInput(BaseModel):
    """Input for add_jira_comment tool."""
    issue_key: str = Field(description="The Jira issue key")
    comment: str = Field(description="Comment text to add")


class GetJiraTransitionsInput(BaseModel):
    """Input for get_jira_transitions tool."""
    issue_key: str = Field(description="The Jira issue key")


class TransitionJiraIssueInput(BaseModel):
    """Input for transition_jira_issue tool."""
    issue_key: str = Field(description="The Jira issue key")
    transition_id: str = Field(description="The transition ID to execute")


class DownloadJiraAttachmentsInput(BaseModel):
    """Input for download_jira_attachments tool."""
    issue_key: str = Field(description="The Jira issue key")
    types: list[str] = Field(default=["image", "pdf", "csv"], description="Attachment types: image, pdf, csv, all")
    dest_dir: str = Field(default="/tmp", description="Destination directory")


@tool(args_schema=GetJiraIssueInput)
def get_jira_issue(issue_key: str) -> dict:
    """Get details of a Jira issue by key.
    
    Use this tool to fetch issue summary, description, status, assignee, and attachments.
    """
    logger.info(f"Tool get_jira_issue called: issue_key={issue_key}")
    client = get_jira_client()
    return client.get_issue(issue_key)


@tool(args_schema=ListJiraIssuesInput)
def list_jira_issues(status: str = "To Do", limit: int = 10) -> list[dict]:
    """List Jira issues filtered by status.
    
    Use this tool to find issues in a specific status for processing.
    """
    logger.info(f"Tool list_jira_issues called: status={status}, limit={limit}")
    client = get_jira_client()
    return client.list_issues(status=status, limit=limit)


@tool(args_schema=AddJiraCommentInput)
def add_jira_comment(issue_key: str, comment: str) -> dict:
    """Add a comment to a Jira issue.
    
    Use this tool to provide status updates or notes on an issue.
    """
    logger.info(f"Tool add_jira_comment called: issue_key={issue_key}")
    client = get_jira_client()
    return client.add_comment(issue_key, comment)


@tool(args_schema=GetJiraTransitionsInput)
def get_jira_transitions(issue_key: str) -> list[dict]:
    """Get available status transitions for a Jira issue.
    
    Use this tool to find valid transition IDs before changing issue status.
    """
    logger.info(f"Tool get_jira_transitions called: issue_key={issue_key}")
    client = get_jira_client()
    return client.get_transitions(issue_key)


@tool(args_schema=TransitionJiraIssueInput)
def transition_jira_issue(issue_key: str, transition_id: str) -> dict:
    """Transition a Jira issue to a new status.
    
    Use this tool to move issues through workflow stages (e.g., To Do -> In Progress -> Done).
    """
    logger.info(f"Tool transition_jira_issue called: issue_key={issue_key}, transition_id={transition_id}")
    client = get_jira_client()
    return client.transition_issue(issue_key, transition_id)


@tool(args_schema=DownloadJiraAttachmentsInput)
def download_jira_attachments(
    issue_key: str,
    types: list[str] = None,
    dest_dir: str = "/tmp",
) -> list[str]:
    """Download attachments from a Jira issue.
    
    Use this tool to get images, PDFs, or other files attached to an issue.
    """
    logger.info(f"Tool download_jira_attachments called: issue_key={issue_key}, types={types}")
    client = get_jira_client()
    return client.download_attachments(issue_key, types=types, dest_dir=dest_dir)


JIRA_TOOLS = [
    get_jira_issue,
    list_jira_issues,
    add_jira_comment,
    get_jira_transitions,
    transition_jira_issue,
    download_jira_attachments,
]
