# MCP to LangGraph Tools Mapping

This document maps each MCP server tool to its LangGraph equivalent.

## GitHub MCP → `src/tools/github.py`

### Current MCP Tools (mcps/github/tools.js)

| MCP Tool | Description | LangGraph Tool |
|----------|-------------|----------------|
| `get_repo_info` | Get repository information | `get_repo_info` |
| `create_issue` | Create a GitHub issue | `create_issue` |
| `create_pull_request` | Create a pull request | `create_pull_request` |
| `create_pull_request_comment` | Add comment to PR | `create_pr_comment` |
| `list_pull_requests` | List PRs in repo | `list_pull_requests` |

### New LangGraph Tool Definitions

```python
# src/tools/github.py

from langchain_core.tools import tool
from pydantic import BaseModel, Field

class GetRepoInfoInput(BaseModel):
    owner: str = Field(description="Repository owner/organization")
    repo: str = Field(description="Repository name")

@tool(args_schema=GetRepoInfoInput)
def get_repo_info(owner: str, repo: str) -> dict:
    """Get information about a GitHub repository."""
    ...

class CreatePullRequestInput(BaseModel):
    owner: str = Field(description="Repository owner/organization")
    repo: str = Field(description="Repository name")
    title: str = Field(description="Pull request title")
    body: str = Field(default="", description="Pull request body/description")
    head: str = Field(description="Branch to merge from (source branch)")
    base: str = Field(default="main", description="Branch to merge into")

@tool(args_schema=CreatePullRequestInput)
def create_pull_request(owner: str, repo: str, title: str, body: str, head: str, base: str = "main") -> dict:
    """Create a new pull request in a GitHub repository."""
    ...

class CreatePRCommentInput(BaseModel):
    owner: str = Field(description="Repository owner/organization")
    repo: str = Field(description="Repository name")
    pull_number: int = Field(description="Pull request number")
    body: str = Field(description="Comment text content")

@tool(args_schema=CreatePRCommentInput)
def create_pr_comment(owner: str, repo: str, pull_number: int, body: str) -> dict:
    """Add a comment to an existing pull request."""
    ...

class ListPullRequestsInput(BaseModel):
    owner: str = Field(description="Repository owner/organization")
    repo: str = Field(description="Repository name")
    state: str = Field(default="open", description="PR state: open, closed, all")
    limit: int = Field(default=10, description="Maximum number of PRs to return")

@tool(args_schema=ListPullRequestsInput)
def list_pull_requests(owner: str, repo: str, state: str = "open", limit: int = 10) -> list[dict]:
    """List pull requests in a GitHub repository."""
    ...

GITHUB_TOOLS = [get_repo_info, create_issue, create_pull_request, create_pr_comment, list_pull_requests]
```

---

## Jira MCP → `src/tools/jira.py`

### Current MCP Tools (mcps/jira/tools.js)

| MCP Tool | Description | LangGraph Tool |
|----------|-------------|----------------|
| `get_task` | Get Jira task details | `get_jira_issue` |
| `list_tasks` | List Jira tasks by status | `list_jira_issues` |
| `add_comment` | Add comment to task | `add_jira_comment` |
| `get_transitions` | Get available transitions | `get_jira_transitions` |
| `transition_task_status` | Change task status | `transition_jira_issue` |
| `download_image_attachments` | Download image attachments | `download_jira_attachments` |
| `download_attachments` | Download attachments by type | `download_jira_attachments` |

### New LangGraph Tool Definitions

```python
# src/tools/jira.py

from langchain_core.tools import tool
from pydantic import BaseModel, Field

class GetJiraIssueInput(BaseModel):
    issue_key: str = Field(description="The Jira issue key (e.g., DP-4)")

@tool(args_schema=GetJiraIssueInput)
def get_jira_issue(issue_key: str) -> dict:
    """Get details of a Jira issue by key."""
    ...

class ListJiraIssuesInput(BaseModel):
    status: str = Field(default="To Do", description="Filter by status")
    limit: int = Field(default=10, description="Maximum results")

@tool(args_schema=ListJiraIssuesInput)
def list_jira_issues(status: str = "To Do", limit: int = 10) -> list[dict]:
    """List Jira issues filtered by status."""
    ...

class AddJiraCommentInput(BaseModel):
    issue_key: str = Field(description="The Jira issue key")
    comment: str = Field(description="Comment text to add")

@tool(args_schema=AddJiraCommentInput)
def add_jira_comment(issue_key: str, comment: str) -> dict:
    """Add a comment to a Jira issue."""
    ...

class GetJiraTransitionsInput(BaseModel):
    issue_key: str = Field(description="The Jira issue key")

@tool(args_schema=GetJiraTransitionsInput)
def get_jira_transitions(issue_key: str) -> list[dict]:
    """Get available status transitions for a Jira issue."""
    ...

class TransitionJiraIssueInput(BaseModel):
    issue_key: str = Field(description="The Jira issue key")
    transition_id: str = Field(description="The transition ID to execute")

@tool(args_schema=TransitionJiraIssueInput)
def transition_jira_issue(issue_key: str, transition_id: str) -> dict:
    """Transition a Jira issue to a new status."""
    ...

class DownloadJiraAttachmentsInput(BaseModel):
    issue_key: str = Field(description="The Jira issue key")
    types: list[str] = Field(default=["image", "pdf", "csv"], description="Attachment types")
    dest_dir: str = Field(default="/tmp", description="Destination directory")

@tool(args_schema=DownloadJiraAttachmentsInput)
def download_jira_attachments(issue_key: str, types: list[str] = None, dest_dir: str = "/tmp") -> dict:
    """Download attachments from a Jira issue."""
    ...

JIRA_TOOLS = [get_jira_issue, list_jira_issues, add_jira_comment, get_jira_transitions, transition_jira_issue, download_jira_attachments]
```

---

## Discord MCP → `src/tools/discord.py`

### Current MCP Tools (mcps/discord/tools.js)

| MCP Tool | Description | LangGraph Tool |
|----------|-------------|----------------|
| `send_webhook_message` | Send plain message | `send_discord_message` |
| `send_embed_message` | Send embed message | `send_discord_embed` |
| `send_notification` | Send formatted notification | `send_discord_notification` |

### New LangGraph Tool Definitions

```python
# src/tools/discord.py

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Literal

class SendDiscordMessageInput(BaseModel):
    content: str = Field(description="Message content to send")
    username: str = Field(default=None, description="Username to display")

@tool(args_schema=SendDiscordMessageInput)
def send_discord_message(content: str, username: str = None) -> dict:
    """Send a message to Discord via webhook."""
    ...

class SendDiscordEmbedInput(BaseModel):
    title: str = Field(description="Embed title")
    description: str = Field(description="Embed description")
    color: int = Field(default=None, description="Embed color (decimal)")
    url: str = Field(default=None, description="Embed URL")

@tool(args_schema=SendDiscordEmbedInput)
def send_discord_embed(title: str, description: str, color: int = None, url: str = None) -> dict:
    """Send an embed message to Discord via webhook."""
    ...

class SendDiscordNotificationInput(BaseModel):
    type: Literal["info", "success", "warning", "error"] = Field(description="Notification type")
    message: str = Field(description="Notification message")
    details: str = Field(default=None, description="Additional details")

@tool(args_schema=SendDiscordNotificationInput)
def send_discord_notification(type: str, message: str, details: str = None) -> dict:
    """Send a formatted notification to Discord."""
    ...

DISCORD_TOOLS = [send_discord_message, send_discord_embed, send_discord_notification]
```

---

## New Tools (Not in MCP)

### Filesystem Tools (`src/tools/filesystem.py`)

```python
class ReadFileInput(BaseModel):
    path: str = Field(description="Path to file")

@tool(args_schema=ReadFileInput)
def read_file(path: str) -> str:
    """Read contents of a file."""
    ...

class WriteFileInput(BaseModel):
    path: str = Field(description="Path to file")
    content: str = Field(description="Content to write")

@tool(args_schema=WriteFileInput)
def write_file(path: str, content: str) -> dict:
    """Write content to a file."""
    ...

class RunCommandInput(BaseModel):
    command: str = Field(description="Command to run")
    cwd: str = Field(default=None, description="Working directory")

@tool(args_schema=RunCommandInput)
def run_command(command: str, cwd: str = None) -> dict:
    """Run a shell command."""
    ...

FILESYSTEM_TOOLS = [read_file, write_file, run_command]
```

---

## Tool → Agent Mapping

| Agent | Tools Used |
|-------|------------|
| **Planner** | `get_jira_issue`, `get_jira_transitions` |
| **Implementer** | `run_command` (git clone, branch), `read_file`, `write_file` |
| **Tester** | `run_command` (npm test), `read_file`, `write_file` |
| **Reporter** | `run_command` (git commit/push), `create_pull_request`, `create_pr_comment`, `transition_jira_issue`, `add_jira_comment`, `send_discord_notification` |

---

## Environment Variables

All tools will use these environment variables (same as MCP servers):

```bash
# GitHub
GITHUB_TOKEN=your_github_token
GITHUB_OWNER=your_github_owner
GITHUB_REPO=boilerplate-react-app

# Jira
JIRA_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your_email@example.com
JIRA_API_TOKEN=your_jira_api_token
JIRA_PROJECT=YOURPROJ

# Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# LLM
OPENAI_API_KEY=your_openai_api_key
```
