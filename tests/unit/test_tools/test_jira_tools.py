"""Tests for Jira tools."""

import pytest
from unittest.mock import patch

from src.tools.jira import (
    get_jira_issue,
    list_jira_issues,
    add_jira_comment,
    get_jira_transitions,
    transition_jira_issue,
)
from tests.mocks.mock_jira import MockJiraClient, MOCK_ISSUE, MOCK_TRANSITIONS


class TestJiraTools:
    """Tests for Jira LangChain tools."""
    
    @patch("src.tools.jira.get_jira_client")
    def test_get_jira_issue(self, mock_get_client):
        client = MockJiraClient()
        mock_get_client.return_value = client
        
        result = get_jira_issue.invoke({"issue_key": "DP-123"})
        
        assert result["key"] == "DP-123"
        assert "fields" in result
        assert ("get_issue", "DP-123") in client.calls
    
    @patch("src.tools.jira.get_jira_client")
    def test_list_jira_issues(self, mock_get_client):
        client = MockJiraClient()
        mock_get_client.return_value = client
        
        result = list_jira_issues.invoke({"status": "To Do", "limit": 5})
        
        assert len(result) == 1
        assert ("list_issues", "To Do", 5) in client.calls
    
    @patch("src.tools.jira.get_jira_client")
    def test_add_jira_comment(self, mock_get_client):
        client = MockJiraClient()
        mock_get_client.return_value = client
        
        result = add_jira_comment.invoke({
            "issue_key": "DP-123",
            "comment": "Test comment",
        })
        
        assert result["body"] == "Test comment"
        assert ("add_comment", "DP-123", "Test comment") in client.calls
    
    @patch("src.tools.jira.get_jira_client")
    def test_get_jira_transitions(self, mock_get_client):
        client = MockJiraClient()
        mock_get_client.return_value = client
        
        result = get_jira_transitions.invoke({"issue_key": "DP-123"})
        
        assert len(result) == 2
        assert result[0]["name"] == "In Review"
        assert ("get_transitions", "DP-123") in client.calls
    
    @patch("src.tools.jira.get_jira_client")
    def test_transition_jira_issue(self, mock_get_client):
        client = MockJiraClient()
        mock_get_client.return_value = client
        
        result = transition_jira_issue.invoke({
            "issue_key": "DP-123",
            "transition_id": "21",
        })
        
        assert result["success"] is True
        assert ("transition_issue", "DP-123", "21") in client.calls
