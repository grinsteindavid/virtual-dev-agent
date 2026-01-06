"""GitHub LangChain tools."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.clients.github_client import get_github_client
from src.logger import get_logger

logger = get_logger(__name__)


class GetRepoInfoInput(BaseModel):
    """Input for get_repo_info tool."""
    owner: str = Field(description="Repository owner/organization")
    repo: str = Field(description="Repository name")


class CreateIssueInput(BaseModel):
    """Input for create_issue tool."""
    title: str = Field(description="Issue title")
    body: str = Field(default="", description="Issue body/description")
    owner: str = Field(default=None, description="Repository owner (optional, uses config default)")
    repo: str = Field(default=None, description="Repository name (optional, uses config default)")


class CreatePullRequestInput(BaseModel):
    """Input for create_pull_request tool."""
    title: str = Field(description="Pull request title")
    head: str = Field(description="Branch to merge from (source branch)")
    base: str = Field(default="main", description="Branch to merge into (target branch)")
    body: str = Field(default="", description="Pull request body/description")
    owner: str = Field(default=None, description="Repository owner (optional)")
    repo: str = Field(default=None, description="Repository name (optional)")


class CreatePRCommentInput(BaseModel):
    """Input for create_pr_comment tool."""
    pull_number: int = Field(description="Pull request number")
    body: str = Field(description="Comment text content")
    owner: str = Field(default=None, description="Repository owner (optional)")
    repo: str = Field(default=None, description="Repository name (optional)")


class ListPullRequestsInput(BaseModel):
    """Input for list_pull_requests tool."""
    state: str = Field(default="open", description="PR state: open, closed, all")
    limit: int = Field(default=10, description="Maximum number of PRs to return")
    owner: str = Field(default=None, description="Repository owner (optional)")
    repo: str = Field(default=None, description="Repository name (optional)")


@tool(args_schema=GetRepoInfoInput)
def get_repo_info(owner: str, repo: str) -> dict:
    """Get information about a GitHub repository.
    
    Use this tool to fetch repository details like description, language, stars, etc.
    """
    logger.info(f"Tool get_repo_info called: owner={owner}, repo={repo}")
    client = get_github_client()
    return client.get_repo(owner=owner, repo=repo)


@tool(args_schema=CreateIssueInput)
def create_issue(title: str, body: str = "", owner: str = None, repo: str = None) -> dict:
    """Create a new GitHub issue.
    
    Use this tool to create issues for tracking bugs, features, or tasks.
    """
    logger.info(f"Tool create_issue called: title={title[:50]}")
    client = get_github_client()
    return client.create_issue(title=title, body=body, owner=owner, repo=repo)


@tool(args_schema=CreatePullRequestInput)
def create_pull_request(
    title: str,
    head: str,
    base: str = "main",
    body: str = "",
    owner: str = None,
    repo: str = None,
) -> dict:
    """Create a new pull request in a GitHub repository.
    
    Use this tool after pushing changes to create a PR for code review.
    """
    logger.info(f"Tool create_pull_request called: title={title[:50]}, head={head}, base={base}")
    client = get_github_client()
    return client.create_pull_request(
        title=title, head=head, base=base, body=body, owner=owner, repo=repo
    )


@tool(args_schema=CreatePRCommentInput)
def create_pr_comment(
    pull_number: int,
    body: str,
    owner: str = None,
    repo: str = None,
) -> dict:
    """Add a comment to an existing pull request.
    
    Use this tool to add status updates or review comments to PRs.
    """
    logger.info(f"Tool create_pr_comment called: pull_number={pull_number}")
    client = get_github_client()
    return client.create_pr_comment(
        pull_number=pull_number, body=body, owner=owner, repo=repo
    )


@tool(args_schema=ListPullRequestsInput)
def list_pull_requests(
    state: str = "open",
    limit: int = 10,
    owner: str = None,
    repo: str = None,
) -> list[dict]:
    """List pull requests in a GitHub repository.
    
    Use this tool to check for existing PRs, especially before creating new ones.
    """
    logger.info(f"Tool list_pull_requests called: state={state}, limit={limit}")
    client = get_github_client()
    return client.list_pull_requests(state=state, limit=limit, owner=owner, repo=repo)


GITHUB_TOOLS = [
    get_repo_info,
    create_issue,
    create_pull_request,
    create_pr_comment,
    list_pull_requests,
]
