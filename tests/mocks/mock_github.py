"""Mock GitHub client for unit tests."""

MOCK_REPO = {
    "full_name": "owner/repo",
    "description": "Test repository",
    "language": "JavaScript",
    "stargazers_count": 10,
    "forks_count": 5,
    "open_issues_count": 2,
    "html_url": "https://github.com/owner/repo",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-02T00:00:00Z",
}

MOCK_PR = {
    "number": 42,
    "title": "feat: implement DP-123",
    "state": "open",
    "html_url": "https://github.com/owner/repo/pull/42",
    "head": {"ref": "DP-123"},
    "base": {"ref": "main"},
    "user": {"login": "developer"},
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-02T00:00:00Z",
}

MOCK_ISSUE = {
    "number": 1,
    "title": "Test issue",
    "html_url": "https://github.com/owner/repo/issues/1",
    "state": "open",
}

MOCK_COMMENT = {
    "id": 12345,
    "html_url": "https://github.com/owner/repo/pull/42#issuecomment-12345",
    "body": "Test comment",
}


class MockGitHubClient:
    """Mock GitHub client - no network calls."""
    
    def __init__(self):
        self.calls = []
    
    def get_repo(self, owner: str = None, repo: str = None) -> dict:
        self.calls.append(("get_repo", owner, repo))
        return MOCK_REPO
    
    def create_issue(self, title: str, body: str = "", owner: str = None, repo: str = None) -> dict:
        self.calls.append(("create_issue", title, body, owner, repo))
        return {**MOCK_ISSUE, "title": title}
    
    def create_pull_request(
        self,
        title: str,
        head: str,
        base: str = "main",
        body: str = "",
        owner: str = None,
        repo: str = None,
    ) -> dict:
        self.calls.append(("create_pull_request", title, head, base, owner, repo))
        return {**MOCK_PR, "title": title, "head": {"ref": head}, "base": {"ref": base}}
    
    def create_pr_comment(
        self,
        pull_number: int,
        body: str,
        owner: str = None,
        repo: str = None,
    ) -> dict:
        self.calls.append(("create_pr_comment", pull_number, body, owner, repo))
        return {**MOCK_COMMENT, "body": body}
    
    def list_pull_requests(
        self,
        state: str = "open",
        limit: int = 10,
        owner: str = None,
        repo: str = None,
    ) -> list[dict]:
        self.calls.append(("list_pull_requests", state, limit, owner, repo))
        return [MOCK_PR]
    
    def get_pr_comments(
        self,
        pull_number: int,
        limit: int = 20,
        owner: str = None,
        repo: str = None,
    ) -> list[dict]:
        self.calls.append(("get_pr_comments", pull_number, limit, owner, repo))
        return [
            {"id": 1, "user": "reviewer", "body": "Looks good!", "created_at": "2024-01-01T00:00:00Z"},
        ]
    
    def get_pr_review_comments(
        self,
        pull_number: int,
        limit: int = 30,
        owner: str = None,
        repo: str = None,
    ) -> list[dict]:
        self.calls.append(("get_pr_review_comments", pull_number, limit, owner, repo))
        return [
            {"id": 2, "user": "reviewer", "body": "Add tests here", "path": "src/Component.jsx", "line": 10, "created_at": "2024-01-01T00:00:00Z"},
        ]
    
    def close(self):
        pass
