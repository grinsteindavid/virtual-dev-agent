"""Tests for GitHubClient."""

import pytest
from unittest.mock import patch, MagicMock

from src.clients.github_client import GitHubClient, get_github_client


class TestGitHubClient:
    """Tests for GitHub API client."""
    
    @patch("src.clients.github_client.httpx.Client")
    def test_get_repo_returns_formatted_response(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "full_name": "owner/repo",
            "description": "Test repo",
            "language": "Python",
            "stargazers_count": 100,
            "forks_count": 20,
            "open_issues_count": 5,
            "html_url": "https://github.com/owner/repo",
            "created_at": "2024-01-01",
            "updated_at": "2024-01-02",
        }
        mock_client.request.return_value = mock_response
        
        client = GitHubClient(token="test-token", owner="owner", repo="repo")
        result = client.get_repo()
        
        assert result["full_name"] == "owner/repo"
        assert result["language"] == "Python"
    
    @patch("src.clients.github_client.httpx.Client")
    def test_create_issue_returns_issue(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "number": 42,
            "title": "Test issue",
            "html_url": "https://github.com/owner/repo/issues/42",
            "state": "open",
        }
        mock_client.request.return_value = mock_response
        
        client = GitHubClient(token="test-token", owner="owner", repo="repo")
        result = client.create_issue(title="Test issue", body="Body")
        
        assert result["number"] == 42
        assert result["title"] == "Test issue"
    
    @patch("src.clients.github_client.httpx.Client")
    def test_create_pull_request_returns_pr(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "number": 123,
            "title": "feat: new feature",
            "html_url": "https://github.com/owner/repo/pull/123",
            "state": "open",
            "head": {"ref": "feature-branch"},
            "base": {"ref": "main"},
        }
        mock_client.request.return_value = mock_response
        
        client = GitHubClient(token="test-token", owner="owner", repo="repo")
        result = client.create_pull_request(
            title="feat: new feature",
            head="feature-branch",
            base="main",
            body="PR description",
        )
        
        assert result["number"] == 123
        assert result["head"]["ref"] == "feature-branch"
        assert result["base"]["ref"] == "main"
    
    @patch("src.clients.github_client.httpx.Client")
    def test_create_pr_comment_returns_comment(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 12345,
            "html_url": "https://github.com/owner/repo/pull/123#issuecomment-12345",
            "body": "Test comment",
        }
        mock_client.request.return_value = mock_response
        
        client = GitHubClient(token="test-token", owner="owner", repo="repo")
        result = client.create_pr_comment(pull_number=123, body="Test comment")
        
        assert result["id"] == 12345
        assert result["body"] == "Test comment"
    
    @patch("src.clients.github_client.httpx.Client")
    def test_list_pull_requests_returns_list(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "number": 1,
                "title": "PR 1",
                "state": "open",
                "html_url": "https://github.com/owner/repo/pull/1",
                "head": {"ref": "branch-1"},
                "base": {"ref": "main"},
                "user": {"login": "dev1"},
                "created_at": "2024-01-01",
                "updated_at": "2024-01-02",
            },
            {
                "number": 2,
                "title": "PR 2",
                "state": "open",
                "html_url": "https://github.com/owner/repo/pull/2",
                "head": {"ref": "branch-2"},
                "base": {"ref": "main"},
                "user": {"login": "dev2"},
                "created_at": "2024-01-01",
                "updated_at": "2024-01-02",
            },
        ]
        mock_client.request.return_value = mock_response
        
        client = GitHubClient(token="test-token", owner="owner", repo="repo")
        result = client.list_pull_requests(state="open", limit=10)
        
        assert len(result) == 2
        assert result[0]["number"] == 1
        assert result[1]["user"]["login"] == "dev2"
    
    @patch("src.clients.github_client.httpx.Client")
    def test_request_handles_204_response(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_client.request.return_value = mock_response
        
        client = GitHubClient(token="test-token", owner="owner", repo="repo")
        result = client._request("DELETE", "/repos/owner/repo/issues/1")
        
        assert result["success"] is True
    
    @patch("src.clients.github_client.httpx.Client")
    def test_close_closes_client(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        client = GitHubClient(token="test-token", owner="owner", repo="repo")
        client.close()
        
        mock_client.close.assert_called_once()


class TestGetGitHubClient:
    """Tests for singleton pattern."""
    
    def test_returns_client_instance(self):
        from src.clients import github_client
        
        github_client._github_client = None
        
        with patch.object(GitHubClient, "__init__", return_value=None):
            client = get_github_client()
            assert client is not None
