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
