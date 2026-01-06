"""Tests for ReporterAgent."""

import pytest

from src.agents.state import AgentState
from src.agents.reporter import ReporterAgent
from tests.mocks.mock_github import MockGitHubClient, MOCK_PR
from tests.mocks.mock_jira import MockJiraClient
from tests.mocks.mock_discord import MockDiscordClient


class TestReporterAgent:
    """Tests for reporter agent."""
    
    def test_updates_jira_with_comment(self, mock_github, mock_jira, mock_discord):
        agent = ReporterAgent(
            github_client=mock_github,
            jira_client=mock_jira,
            discord_client=mock_discord,
        )
        state = AgentState(
            jira_ticket_id="DP-123",
            jira_details={"fields": {"summary": "Test feature"}},
            branch_name="DP-123",
            repo_path="/tmp/test",
            code_changes=[{"file": "test.js"}],
            test_results={"success": True, "passed": 5, "failed": 0},
        )
        
        agent._update_jira(state)
        
        comment_calls = [c for c in mock_jira.calls if c[0] == "add_comment"]
        assert len(comment_calls) == 1
        assert comment_calls[0][1] == "DP-123"
    
    def test_transitions_jira_to_review(self, mock_github, mock_jira, mock_discord):
        agent = ReporterAgent(
            github_client=mock_github,
            jira_client=mock_jira,
            discord_client=mock_discord,
        )
        state = AgentState(
            jira_ticket_id="DP-123",
            jira_details={"fields": {"summary": "Test"}},
        )
        
        agent._update_jira(state)
        
        transition_calls = [c for c in mock_jira.calls if c[0] == "transition_issue"]
        assert len(transition_calls) == 1
        assert transition_calls[0][2] == "21"
    
    def test_sends_discord_notification(self, mock_github, mock_jira, mock_discord):
        agent = ReporterAgent(
            github_client=mock_github,
            jira_client=mock_jira,
            discord_client=mock_discord,
        )
        state = AgentState(
            jira_ticket_id="DP-123",
            jira_details={"fields": {"summary": "Test feature"}},
            pr_url="https://github.com/owner/repo/pull/42",
            code_changes=[{"file": "test.js"}],
            test_results={"passed": 5, "failed": 0},
        )
        
        agent._send_discord_notification(state)
        
        notification_calls = [c for c in mock_discord.calls if c[0] == "send_notification"]
        assert len(notification_calls) == 1
        assert notification_calls[0][1] == "success"
    
    def test_creates_new_pr_when_none_exists(self, mock_jira, mock_discord):
        mock_github = MockGitHubClient()
        mock_github.list_pull_requests = lambda **kwargs: []
        
        agent = ReporterAgent(
            github_client=mock_github,
            jira_client=mock_jira,
            discord_client=mock_discord,
        )
        state = AgentState(
            jira_ticket_id="DP-123",
            jira_details={"fields": {"summary": "New feature"}},
            branch_name="DP-123",
            code_changes=[{"file": "test.js"}],
            test_results={"passed": 3, "failed": 0},
            implementation_plan="Test plan",
        )
        
        result = agent._create_or_update_pr(state)
        
        assert result is not None
        assert result["number"] == 42
        pr_calls = [c for c in mock_github.calls if c[0] == "create_pull_request"]
        assert len(pr_calls) == 1
    
    def test_comments_on_existing_pr(self, mock_jira, mock_discord):
        existing_pr = {**MOCK_PR, "head": {"ref": "DP-123"}}
        mock_github = MockGitHubClient()
        mock_github.list_pull_requests = lambda **kwargs: [existing_pr]
        
        agent = ReporterAgent(
            github_client=mock_github,
            jira_client=mock_jira,
            discord_client=mock_discord,
        )
        state = AgentState(
            jira_ticket_id="DP-123",
            jira_details={"fields": {"summary": "Existing feature"}},
            branch_name="DP-123",
            test_results={"passed": 5, "failed": 0},
            test_iterations=1,
        )
        
        result = agent._create_or_update_pr(state)
        
        assert result["number"] == 42
        comment_calls = [c for c in mock_github.calls if c[0] == "create_pr_comment"]
        assert len(comment_calls) == 1
