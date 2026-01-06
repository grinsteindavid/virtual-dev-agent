"""Tests for JiraClient."""

import pytest
from unittest.mock import patch, MagicMock

from src.clients.jira_client import JiraClient, get_jira_client


class TestJiraClient:
    """Tests for Jira API client."""
    
    @patch("src.clients.jira_client.httpx.Client")
    def test_get_issue_returns_formatted_response(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "10001",
            "key": "DP-123",
            "fields": {
                "summary": "Test issue",
                "description": "Description",
                "status": {"name": "To Do"},
                "assignee": {"displayName": "Dev"},
                "priority": {"name": "High"},
                "created": "2024-01-01",
                "updated": "2024-01-02",
                "attachment": [],
                "comment": {},
            },
        }
        mock_client.request.return_value = mock_response
        
        client = JiraClient(
            url="https://test.atlassian.net",
            username="user",
            api_token="token",
            project="PROJ",
        )
        result = client.get_issue("DP-123")
        
        assert result["key"] == "DP-123"
        assert result["fields"]["summary"] == "Test issue"
        assert result["fields"]["status"]["name"] == "To Do"
    
    @patch("src.clients.jira_client.httpx.Client")
    def test_list_issues_returns_list(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "issues": [
                {
                    "key": "DP-1",
                    "fields": {
                        "summary": "Issue 1",
                        "status": {"name": "To Do"},
                        "assignee": None,
                        "priority": {"name": "Medium"},
                    },
                },
                {
                    "key": "DP-2",
                    "fields": {
                        "summary": "Issue 2",
                        "status": {"name": "To Do"},
                        "assignee": None,
                        "priority": None,
                    },
                },
            ],
        }
        mock_client.request.return_value = mock_response
        
        client = JiraClient(
            url="https://test.atlassian.net",
            username="user",
            api_token="token",
            project="PROJ",
        )
        result = client.list_issues(status="To Do", limit=10)
        
        assert len(result) == 2
        assert result[0]["key"] == "DP-1"
    
    @patch("src.clients.jira_client.httpx.Client")
    def test_add_comment_returns_comment(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "10001",
            "body": "Test comment",
        }
        mock_client.request.return_value = mock_response
        
        client = JiraClient(
            url="https://test.atlassian.net",
            username="user",
            api_token="token",
            project="PROJ",
        )
        result = client.add_comment("DP-123", "Test comment")
        
        assert result["id"] == "10001"
        assert result["body"] == "Test comment"
    
    @patch("src.clients.jira_client.httpx.Client")
    def test_get_transitions_returns_list(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "transitions": [
                {"id": "21", "name": "In Review", "to": {"name": "In Review"}},
                {"id": "31", "name": "Done", "to": {"name": "Done"}},
            ],
        }
        mock_client.request.return_value = mock_response
        
        client = JiraClient(
            url="https://test.atlassian.net",
            username="user",
            api_token="token",
            project="PROJ",
        )
        result = client.get_transitions("DP-123")
        
        assert len(result) == 2
        assert result[0]["name"] == "In Review"
    
    @patch("src.clients.jira_client.httpx.Client")
    def test_transition_issue_success(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        transition_response = MagicMock()
        transition_response.status_code = 204
        transition_response.json.return_value = {"success": True}
        
        issue_response = MagicMock()
        issue_response.status_code = 200
        issue_response.json.return_value = {
            "id": "10001",
            "key": "DP-123",
            "fields": {
                "summary": "Test",
                "description": None,
                "status": {"name": "In Review"},
                "assignee": None,
                "priority": None,
                "created": "2024-01-01",
                "updated": "2024-01-02",
                "attachment": [],
                "comment": {},
            },
        }
        
        mock_client.request.side_effect = [transition_response, issue_response]
        
        client = JiraClient(
            url="https://test.atlassian.net",
            username="user",
            api_token="token",
            project="PROJ",
        )
        result = client.transition_issue("DP-123", "21")
        
        assert result["success"] is True
        assert result["new_status"] == "In Review"
    
    @patch("src.clients.jira_client.httpx.Client")
    def test_request_raises_on_http_error(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_client.request.return_value = mock_response
        
        client = JiraClient(
            url="https://test.atlassian.net",
            username="user",
            api_token="token",
            project="PROJ",
        )
        
        with pytest.raises(Exception):
            client._request("GET", "/issue/INVALID")
    
    @patch("src.clients.jira_client.httpx.Client")
    def test_close_closes_client(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        client = JiraClient(
            url="https://test.atlassian.net",
            username="user",
            api_token="token",
            project="PROJ",
        )
        client.close()
        
        mock_client.close.assert_called_once()


class TestGetJiraClient:
    """Tests for singleton pattern."""
    
    def test_returns_client_instance(self):
        from src.clients import jira_client
        
        jira_client._jira_client = None
        
        with patch.object(JiraClient, "__init__", return_value=None):
            client = get_jira_client()
            assert client is not None
