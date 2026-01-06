"""Tests for GitHub tools."""

import pytest
from unittest.mock import patch

from src.tools.github import (
    get_repo_info,
    create_issue,
    create_pull_request,
    create_pr_comment,
    list_pull_requests,
)
from tests.mocks.mock_github import MockGitHubClient, MOCK_REPO, MOCK_PR


class TestGitHubTools:
    """Tests for GitHub LangChain tools."""
    
    @patch("src.tools.github.get_github_client")
    def test_get_repo_info(self, mock_get_client):
        client = MockGitHubClient()
        mock_get_client.return_value = client
        
        result = get_repo_info.invoke({"owner": "owner", "repo": "repo"})
        
        assert result["full_name"] == "owner/repo"
        assert ("get_repo", "owner", "repo") in client.calls
    
    @patch("src.tools.github.get_github_client")
    def test_create_issue(self, mock_get_client):
        client = MockGitHubClient()
        mock_get_client.return_value = client
        
        result = create_issue.invoke({
            "title": "Test issue",
            "body": "Issue body",
        })
        
        assert result["title"] == "Test issue"
        assert len([c for c in client.calls if c[0] == "create_issue"]) == 1
    
    @patch("src.tools.github.get_github_client")
    def test_create_pull_request(self, mock_get_client):
        client = MockGitHubClient()
        mock_get_client.return_value = client
        
        result = create_pull_request.invoke({
            "title": "feat: DP-123",
            "head": "DP-123",
            "base": "main",
            "body": "PR body",
        })
        
        assert result["number"] == 42
        assert result["head"]["ref"] == "DP-123"
        assert result["base"]["ref"] == "main"
    
    @patch("src.tools.github.get_github_client")
    def test_create_pr_comment(self, mock_get_client):
        client = MockGitHubClient()
        mock_get_client.return_value = client
        
        result = create_pr_comment.invoke({
            "pull_number": 42,
            "body": "Test comment",
        })
        
        assert result["id"] == 12345
        assert result["body"] == "Test comment"
    
    @patch("src.tools.github.get_github_client")
    def test_list_pull_requests(self, mock_get_client):
        client = MockGitHubClient()
        mock_get_client.return_value = client
        
        result = list_pull_requests.invoke({
            "state": "open",
            "limit": 10,
        })
        
        assert len(result) == 1
        assert result[0]["number"] == 42
