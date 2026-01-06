"""Tests for PlannerAgent."""

import pytest

from src.agents.state import AgentState
from src.agents.planner import PlannerAgent
from tests.mocks.mock_llm import FakeLLM
from tests.mocks.mock_jira import MockJiraClient


class TestPlannerAgent:
    """Tests for planner agent."""
    
    def test_fetches_jira_and_creates_plan(self, mock_jira, fake_llm):
        fake_llm.response = "1. Create Greeting component\n2. Add PropTypes\n3. Write tests"
        agent = PlannerAgent(jira_client=mock_jira, llm=fake_llm)
        state = AgentState(jira_ticket_id="DP-123")
        
        result = agent.run(state)
        
        assert "Greeting" in result.implementation_plan or result.implementation_plan
        assert ("get_issue", "DP-123") in mock_jira.calls
    
    def test_sets_branch_name_from_ticket(self, mock_jira, fake_llm):
        agent = PlannerAgent(jira_client=mock_jira, llm=fake_llm)
        state = AgentState(jira_ticket_id="DP-456")
        
        result = agent.run(state)
        
        assert result.branch_name == "DP-456"
    
    def test_stores_jira_details_in_state(self, mock_jira, fake_llm):
        agent = PlannerAgent(jira_client=mock_jira, llm=fake_llm)
        state = AgentState(jira_ticket_id="DP-123")
        
        result = agent.run(state)
        
        assert result.jira_details["key"] == "DP-123"
        assert "fields" in result.jira_details
        assert "summary" in result.jira_details["fields"]
    
    def test_sets_status_to_planning(self, mock_jira, fake_llm):
        agent = PlannerAgent(jira_client=mock_jira, llm=fake_llm)
        state = AgentState(jira_ticket_id="DP-123")
        
        result = agent.run(state)
        
        assert result.status == "planning"
    
    def test_creates_default_plan_without_llm(self, mock_jira):
        agent = PlannerAgent(jira_client=mock_jira, llm=None)
        state = AgentState(jira_ticket_id="DP-123")
        
        result = agent.run(state)
        
        assert result.implementation_plan
        assert "Implementation Plan" in result.implementation_plan
    
    def test_handles_jira_error(self):
        class FailingJiraClient:
            def get_issue(self, key):
                raise Exception("Jira API error")
        
        agent = PlannerAgent(jira_client=FailingJiraClient(), llm=None)
        state = AgentState(jira_ticket_id="DP-123")
        
        result = agent.run(state)
        
        assert result.status == "failed"
        assert "Planner error" in result.error
    
    def test_sets_confidence_score(self, mock_jira, fake_llm):
        agent = PlannerAgent(jira_client=mock_jira, llm=fake_llm)
        state = AgentState(jira_ticket_id="DP-123")
        
        result = agent.run(state)
        
        assert result.confidence["planning"] == 0.8
    
    def test_fetches_and_stores_comments(self, mock_jira, fake_llm):
        agent = PlannerAgent(jira_client=mock_jira, llm=fake_llm)
        state = AgentState(jira_ticket_id="DP-123")
        
        result = agent.run(state)
        
        assert ("get_comments", "DP-123", 5) in mock_jira.calls
        assert "recent_comments" in result.jira_details
        assert len(result.jira_details["recent_comments"]) > 0
    
    def test_includes_comments_in_llm_prompt(self, mock_jira, fake_llm):
        fake_llm.response = "Plan with comments considered"
        agent = PlannerAgent(jira_client=mock_jira, llm=fake_llm)
        state = AgentState(jira_ticket_id="DP-123")
        
        agent.run(state)
        
        prompt_content = fake_llm.calls[0][1].content
        assert "Product Owner" in prompt_content or "Recent Comments" in prompt_content
    
    def test_format_comments_returns_empty_for_no_comments(self):
        agent = PlannerAgent(jira_client=None, llm=None)
        result = agent._format_comments([])
        assert result == ""
    
    def test_format_comments_includes_author_and_body(self):
        agent = PlannerAgent(jira_client=None, llm=None)
        comments = [
            {"author": "User1", "body": "Comment text here"},
        ]
        result = agent._format_comments(comments)
        assert "User1" in result
        assert "Comment text" in result
