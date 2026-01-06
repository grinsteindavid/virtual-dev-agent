"""GitHub REST API client."""

import httpx
from src.config import config
from src.logger import get_logger

logger = get_logger(__name__)


class GitHubClient:
    """Client for GitHub REST API."""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: str | None = None, owner: str | None = None, repo: str | None = None):
        self.token = token or config.github.token
        self.owner = owner or config.github.owner
        self.repo = repo or config.github.repo
        self._client = httpx.Client(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=30.0,
        )
    
    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make an HTTP request to GitHub API."""
        response = self._client.request(method, endpoint, **kwargs)
        response.raise_for_status()
        if response.status_code == 204:
            return {"success": True}
        return response.json()
    
    def get_repo(self, owner: str | None = None, repo: str | None = None) -> dict:
        """Get repository information."""
        owner = owner or self.owner
        repo = repo or self.repo
        logger.info(f"get_repo: owner={owner} repo={repo}")
        data = self._request("GET", f"/repos/{owner}/{repo}")
        logger.info(f"get_repo: success full_name={data.get('full_name')}")
        return {
            "full_name": data["full_name"],
            "description": data.get("description"),
            "language": data.get("language"),
            "stargazers_count": data.get("stargazers_count"),
            "forks_count": data.get("forks_count"),
            "open_issues_count": data.get("open_issues_count"),
            "html_url": data.get("html_url"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
        }
    
    def create_issue(self, title: str, body: str = "", owner: str | None = None, repo: str | None = None) -> dict:
        """Create a new issue."""
        owner = owner or self.owner
        repo = repo or self.repo
        logger.info(f"create_issue: owner={owner} repo={repo} title={title[:50]}")
        data = self._request("POST", f"/repos/{owner}/{repo}/issues", json={"title": title, "body": body})
        logger.info(f"create_issue: success number={data.get('number')}")
        return {
            "number": data["number"],
            "title": data["title"],
            "html_url": data["html_url"],
            "state": data["state"],
        }
    
    def create_pull_request(
        self,
        title: str,
        head: str,
        base: str = "main",
        body: str = "",
        owner: str | None = None,
        repo: str | None = None,
    ) -> dict:
        """Create a new pull request."""
        owner = owner or self.owner
        repo = repo or self.repo
        logger.info(f"create_pull_request: owner={owner} repo={repo} title={title[:50]} head={head} base={base}")
        data = self._request(
            "POST",
            f"/repos/{owner}/{repo}/pulls",
            json={"title": title, "body": body, "head": head, "base": base},
        )
        logger.info(f"create_pull_request: success number={data.get('number')} url={data.get('html_url')}")
        return {
            "number": data["number"],
            "title": data["title"],
            "html_url": data["html_url"],
            "state": data["state"],
            "head": {"ref": data["head"]["ref"]},
            "base": {"ref": data["base"]["ref"]},
        }
    
    def create_pr_comment(
        self,
        pull_number: int,
        body: str,
        owner: str | None = None,
        repo: str | None = None,
    ) -> dict:
        """Add a comment to a pull request."""
        owner = owner or self.owner
        repo = repo or self.repo
        logger.info(f"create_pr_comment: owner={owner} repo={repo} pull_number={pull_number}")
        data = self._request(
            "POST",
            f"/repos/{owner}/{repo}/issues/{pull_number}/comments",
            json={"body": body},
        )
        logger.info(f"create_pr_comment: success id={data.get('id')}")
        return {
            "id": data["id"],
            "html_url": data["html_url"],
            "body": data["body"],
        }
    
    def list_pull_requests(
        self,
        state: str = "open",
        limit: int = 10,
        owner: str | None = None,
        repo: str | None = None,
    ) -> list[dict]:
        """List pull requests in a repository."""
        owner = owner or self.owner
        repo = repo or self.repo
        logger.info(f"list_pull_requests: owner={owner} repo={repo} state={state} limit={limit}")
        data = self._request(
            "GET",
            f"/repos/{owner}/{repo}/pulls",
            params={"state": state, "per_page": limit},
        )
        logger.info(f"list_pull_requests: success count={len(data)}")
        return [
            {
                "number": pr["number"],
                "title": pr["title"],
                "state": pr["state"],
                "html_url": pr["html_url"],
                "head": {"ref": pr["head"]["ref"]},
                "base": {"ref": pr["base"]["ref"]},
                "user": {"login": pr["user"]["login"]},
                "created_at": pr["created_at"],
                "updated_at": pr["updated_at"],
            }
            for pr in data
        ]
    
    def get_pr_comments(
        self,
        pull_number: int,
        limit: int = 20,
        owner: str | None = None,
        repo: str | None = None,
    ) -> list[dict]:
        """Get comments on a pull request."""
        owner = owner or self.owner
        repo = repo or self.repo
        logger.info(f"get_pr_comments: owner={owner} repo={repo} pull_number={pull_number}")
        data = self._request(
            "GET",
            f"/repos/{owner}/{repo}/issues/{pull_number}/comments",
            params={"per_page": limit},
        )
        logger.info(f"get_pr_comments: success count={len(data)}")
        return [
            {
                "id": comment["id"],
                "user": comment["user"]["login"],
                "body": comment["body"][:500],
                "created_at": comment["created_at"],
            }
            for comment in data
        ]
    
    def get_pr_review_comments(
        self,
        pull_number: int,
        limit: int = 30,
        owner: str | None = None,
        repo: str | None = None,
    ) -> list[dict]:
        """Get review comments (inline code comments) on a pull request."""
        owner = owner or self.owner
        repo = repo or self.repo
        logger.info(f"get_pr_review_comments: owner={owner} repo={repo} pull_number={pull_number}")
        data = self._request(
            "GET",
            f"/repos/{owner}/{repo}/pulls/{pull_number}/comments",
            params={"per_page": limit},
        )
        logger.info(f"get_pr_review_comments: success count={len(data)}")
        return [
            {
                "id": comment["id"],
                "user": comment["user"]["login"],
                "body": comment["body"][:500],
                "path": comment.get("path", ""),
                "line": comment.get("line"),
                "created_at": comment["created_at"],
            }
            for comment in data
        ]
    
    def close(self):
        """Close the HTTP client."""
        self._client.close()


_github_client: GitHubClient | None = None


def get_github_client() -> GitHubClient:
    """Get or create the GitHub client singleton."""
    global _github_client
    if _github_client is None:
        _github_client = GitHubClient()
    return _github_client
