"""Git operations for repository management."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.config import config
from src.logger import get_logger
from src.tools.filesystem import run_command

logger = get_logger(__name__)


class CloneRepoInput(BaseModel):
    """Input for clone_repo tool."""
    repo_path: str = Field(description="Local path to clone to")
    owner: str = Field(default=None, description="Repository owner")
    repo: str = Field(default=None, description="Repository name")


class ConfigureGitInput(BaseModel):
    """Input for configure_git_user tool."""
    repo_path: str = Field(description="Path to repository")
    email: str = Field(default="virtual-dev@agent.local", description="Git user email")
    name: str = Field(default="Virtual Dev Agent", description="Git user name")


class BranchInput(BaseModel):
    """Input for branch operations."""
    repo_path: str = Field(description="Path to repository")
    branch_name: str = Field(description="Branch name")


class CheckoutBranchInput(BaseModel):
    """Input for checkout_branch tool."""
    repo_path: str = Field(description="Path to repository")
    branch_name: str = Field(description="Branch name")
    create: bool = Field(default=False, description="Create new branch")


class CommitAndPushInput(BaseModel):
    """Input for commit_and_push tool."""
    repo_path: str = Field(description="Path to repository")
    branch_name: str = Field(description="Branch to push")
    commit_message: str = Field(description="Commit message")
    force: bool = Field(default=True, description="Force push")


@tool(args_schema=CloneRepoInput)
def clone_repo(repo_path: str, owner: str = None, repo: str = None) -> dict:
    """Clone a repository to the specified path."""
    owner = owner or config.github.owner
    repo = repo or config.github.repo
    clone_url = f"https://github.com/{owner}/{repo}.git"
    
    logger.info(f"Cloning {owner}/{repo} to {repo_path}")
    result = run_command.invoke({
        "command": f"rm -rf {repo_path} && git clone {clone_url} {repo_path}",
        "timeout": 120,
    })
    
    if not result["success"]:
        return {"success": False, "error": result["stderr"]}
    
    return {"success": True, "repo_path": repo_path}


@tool(args_schema=ConfigureGitInput)
def configure_git_user(repo_path: str, email: str = "virtual-dev@agent.local", name: str = "Virtual Dev Agent") -> dict:
    """Configure git user identity for a repository."""
    run_command.invoke({"command": f'git config user.email "{email}"', "cwd": repo_path})
    run_command.invoke({"command": f'git config user.name "{name}"', "cwd": repo_path})
    logger.info(f"Configured git user: {name} <{email}>")
    return {"success": True}


@tool(args_schema=BranchInput)
def branch_exists_on_remote(repo_path: str, branch_name: str) -> bool:
    """Check if a branch exists on remote."""
    result = run_command.invoke({
        "command": f"git ls-remote --heads origin {branch_name}",
        "cwd": repo_path,
    })
    return bool(result.get("stdout", "").strip())


@tool(args_schema=CheckoutBranchInput)
def checkout_branch(repo_path: str, branch_name: str, create: bool = False) -> dict:
    """Checkout or create a branch."""
    if create:
        logger.info(f"Creating new branch '{branch_name}'")
        cmd = f"git checkout -b {branch_name}"
    else:
        logger.info(f"Checking out existing branch '{branch_name}'")
        cmd = f"git fetch origin {branch_name} && git checkout {branch_name}"
    
    result = run_command.invoke({"command": cmd, "cwd": repo_path})
    return {"success": result["success"], "branch": branch_name}


@tool(args_schema=BranchInput)
def get_commit_log(repo_path: str, branch_name: str = None, limit: int = 10) -> str:
    """Get recent commit log."""
    result = run_command.invoke({
        "command": f"git log --oneline -n {limit}",
        "cwd": repo_path,
    })
    return result.get("stdout", "")[:1000]


@tool(args_schema=CommitAndPushInput)
def commit_and_push(repo_path: str, branch_name: str, commit_message: str, force: bool = True) -> dict:
    """Stage, commit, and push changes."""
    run_command.invoke({"command": "git add -A", "cwd": repo_path})
    
    commit_result = run_command.invoke({
        "command": f'git commit -m "{commit_message}" --allow-empty',
        "cwd": repo_path,
    })
    
    token = config.github.token
    owner = config.github.owner
    repo = config.github.repo
    push_url = f"https://{token}@github.com/{owner}/{repo}.git"
    force_flag = "--force" if force else ""
    
    push_result = run_command.invoke({
        "command": f"git push {push_url} {branch_name} {force_flag}",
        "cwd": repo_path,
        "timeout": 60,
    })
    
    logger.info(f"Push result: success={push_result['success']}")
    return {
        "success": push_result["success"],
        "message": push_result.get("stderr", "") or push_result.get("stdout", ""),
    }


GIT_TOOLS = [
    clone_repo,
    configure_git_user,
    branch_exists_on_remote,
    checkout_branch,
    get_commit_log,
    commit_and_push,
]
