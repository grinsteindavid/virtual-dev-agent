"""Tests for SupervisorAgent."""

import pytest

from src.agents.state import AgentState
from src.agents.supervisor import SupervisorAgent
from tests.mocks.mock_llm import FakeLLM


class TestSupervisorAgent:
    """Tests for supervisor routing logic."""
    
    def test_routes_to_planner_for_new_task(self, routing_llm_planner):
        supervisor = SupervisorAgent(llm=routing_llm_planner)
        state = AgentState(jira_ticket_id="DP-123", status="pending")
        
        result = supervisor.route(state)
        
        assert result.route == "planner"
        assert result.confidence["routing"] == 0.9
        assert len(routing_llm_planner.calls) == 1
    
    def test_routes_to_implementer_after_planning(self, routing_llm_implementer):
        supervisor = SupervisorAgent(llm=routing_llm_implementer)
        state = AgentState(
            jira_ticket_id="DP-123",
            implementation_plan="1. Create component\n2. Add tests",
            status="planning",
        )
        
        result = supervisor.route(state)
        
        assert result.route == "implementer"
    
    def test_routes_to_tester_after_implementation(self, routing_llm_tester):
        supervisor = SupervisorAgent(llm=routing_llm_tester)
        state = AgentState(
            jira_ticket_id="DP-123",
            code_changes=[{"file": "src/Component.jsx", "action": "create"}],
            status="implementing",
        )
        
        result = supervisor.route(state)
        
        assert result.route == "tester"
    
    def test_routes_to_reporter_when_tests_pass(self, routing_llm_reporter):
        supervisor = SupervisorAgent(llm=routing_llm_reporter)
        state = AgentState(
            jira_ticket_id="DP-123",
            test_results={"success": True, "passed": 5, "failed": 0},
            status="testing",
        )
        
        result = supervisor.route(state)
        
        assert result.route == "reporter"
    
    def test_routes_to_done_after_reporting(self, routing_llm_done):
        supervisor = SupervisorAgent(llm=routing_llm_done)
        state = AgentState(
            jira_ticket_id="DP-123",
            pr_url="https://github.com/owner/repo/pull/42",
            status="reporting",
        )
        
        result = supervisor.route(state)
        
        assert result.route == "done"
    
    def test_fallback_to_planner_on_invalid_route(self):
        llm = FakeLLM(response="invalid_response_not_json")
        supervisor = SupervisorAgent(llm=llm)
        state = AgentState(jira_ticket_id="DP-123", status="pending")
        
        result = supervisor.route(state)
        
        assert result.route == "planner"
        assert result.confidence["routing"] == 0.3
    
    def test_fallback_to_tester_when_code_exists(self):
        llm = FakeLLM(response="garbage")
        supervisor = SupervisorAgent(llm=llm)
        state = AgentState(
            jira_ticket_id="DP-123",
            implementation_plan="plan",
            code_changes=[{"file": "test.js"}],
        )
        
        result = supervisor.route(state)
        
        assert result.route == "tester"
    
    def test_fallback_to_reporter_when_tests_passed(self):
        llm = FakeLLM(response="invalid")
        supervisor = SupervisorAgent(llm=llm)
        state = AgentState(
            jira_ticket_id="DP-123",
            code_changes=[{"file": "test.js"}],
            test_results={"success": True},
        )
        
        result = supervisor.route(state)
        
        assert result.route == "reporter"
    
    def test_max_test_iterations_routes_to_reporter(self):
        llm = FakeLLM(response='{"route": "tester", "confidence": 0.9}')
        supervisor = SupervisorAgent(llm=llm)
        state = AgentState(
            jira_ticket_id="DP-123",
            test_iterations=3,
            test_results={"success": False},
        )
        
        result = supervisor.route(state)
        
        assert result.route == "reporter"
    
    def test_handles_uppercase_route(self):
        llm = FakeLLM(response='{"route": "PLANNER", "confidence": 0.8}')
        supervisor = SupervisorAgent(llm=llm)
        state = AgentState(jira_ticket_id="DP-123")
        
        result = supervisor.route(state)
        
        assert result.route == "planner"
    
    def test_fallback_to_tester_when_skip_implementation(self):
        llm = FakeLLM(response="garbage")
        supervisor = SupervisorAgent(llm=llm)
        state = AgentState(
            jira_ticket_id="DP-123",
            implementation_plan="plan",
            skip_implementation=True,
        )
        
        result = supervisor.route(state)
        
        assert result.route == "tester"
    
    def test_fallback_to_implementer_with_fix_suggestions(self):
        llm = FakeLLM(response="invalid")
        supervisor = SupervisorAgent(llm=llm)
        state = AgentState(
            jira_ticket_id="DP-123",
            implementation_plan="plan",
            code_changes=[{"file": "test.js"}],
            test_results={"success": False},
            fix_suggestions="Fix the import statement",
        )
        
        result = supervisor.route(state)
        
        assert result.route == "implementer"
