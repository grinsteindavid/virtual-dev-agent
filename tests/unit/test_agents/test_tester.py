"""Tests for TesterAgent."""

import pytest
from unittest.mock import patch, MagicMock

from src.agents.state import AgentState
from src.agents.tester import TesterAgent
from tests.mocks.mock_llm import FakeLLM


class TestTesterAgent:
    """Tests for tester agent."""
    
    @patch("src.agents.tester.run_command")
    def test_run_tests_success(self, mock_run_command):
        mock_run_command.invoke.return_value = {
            "success": True,
            "stdout": "Tests: 5 passed, 0 failed",
            "stderr": "",
        }
        
        agent = TesterAgent(llm=None)
        state = AgentState(
            jira_ticket_id="DP-123",
            repo_path="/tmp/project",
            code_changes=[{"file": "test.js"}],
        )
        
        result = agent.run(state)
        
        assert result.test_results["success"] is True
        assert result.test_results["passed"] == 5
        assert result.test_results["failed"] == 0
        assert result.status == "testing"
        assert result.confidence["testing"] == 0.9
    
    @patch("src.agents.tester.run_command")
    def test_run_tests_failure(self, mock_run_command):
        mock_run_command.invoke.return_value = {
            "success": False,
            "stdout": "Tests: 3 passed, 2 failed",
            "stderr": "FAIL src/Component.test.js",
        }
        
        agent = TesterAgent(llm=None)
        state = AgentState(
            jira_ticket_id="DP-123",
            repo_path="/tmp/project",
            code_changes=[{"file": "test.js"}],
        )
        
        result = agent.run(state)
        
        assert result.test_results["success"] is False
        assert result.test_results["passed"] == 3
        assert result.test_results["failed"] == 2
        assert result.confidence["testing"] == 0.5
    
    @patch("src.agents.tester.run_command")
    def test_increments_iteration_counter(self, mock_run_command):
        mock_run_command.invoke.return_value = {
            "success": True,
            "stdout": "Tests: 1 passed",
            "stderr": "",
        }
        
        agent = TesterAgent(llm=None)
        state = AgentState(
            jira_ticket_id="DP-123",
            repo_path="/tmp/project",
            test_iterations=0,
        )
        
        result = agent.run(state)
        
        assert result.test_iterations == 1
    
    @patch("src.agents.tester.run_command")
    def test_attempt_fix_called_on_failure_with_llm(self, mock_run_command):
        mock_run_command.invoke.return_value = {
            "success": False,
            "stdout": "Tests: 0 passed, 1 failed",
            "stderr": "Error in test",
        }
        
        fake_llm = FakeLLM(response="Fix suggestion: update the component")
        agent = TesterAgent(llm=fake_llm)
        state = AgentState(
            jira_ticket_id="DP-123",
            repo_path="/tmp/project",
            code_changes=[{"file": "src/test.js", "content": "code"}],
            test_iterations=0,
        )
        
        result = agent.run(state)
        
        assert len(fake_llm.calls) == 1
    
    @patch("src.agents.tester.run_command")
    def test_no_fix_attempt_without_llm(self, mock_run_command):
        mock_run_command.invoke.return_value = {
            "success": False,
            "stdout": "Tests: 0 passed, 1 failed",
            "stderr": "",
        }
        
        agent = TesterAgent(llm=None)
        state = AgentState(
            jira_ticket_id="DP-123",
            repo_path="/tmp/project",
            test_iterations=0,
        )
        
        result = agent.run(state)
        
        assert result.test_results["success"] is False
    
    @patch("src.agents.tester.run_command")
    def test_no_fix_attempt_at_max_iterations(self, mock_run_command):
        mock_run_command.invoke.return_value = {
            "success": False,
            "stdout": "Tests: 0 passed, 1 failed",
            "stderr": "",
        }
        
        fake_llm = FakeLLM(response="Fix")
        agent = TesterAgent(llm=fake_llm)
        state = AgentState(
            jira_ticket_id="DP-123",
            repo_path="/tmp/project",
            test_iterations=2,
            code_changes=[{"file": "test.js", "content": "code"}],
        )
        
        result = agent.run(state)
        
        assert len(fake_llm.calls) == 0
    
    @patch("src.agents.tester.run_command")
    def test_parses_test_output_correctly(self, mock_run_command):
        mock_run_command.invoke.return_value = {
            "success": True,
            "stdout": """
PASS src/components/Widget.test.js
PASS src/utils/helper.test.js

Tests: 12 passed, 0 failed
Time: 2.5s
""",
            "stderr": "",
        }
        
        agent = TesterAgent(llm=None)
        state = AgentState(
            jira_ticket_id="DP-123",
            repo_path="/tmp/project",
        )
        
        result = agent.run(state)
        
        assert result.test_results["passed"] == 12
        assert result.test_results["failed"] == 0
    
    @patch("src.agents.tester.run_command")
    def test_handles_exception(self, mock_run_command):
        mock_run_command.invoke.side_effect = Exception("Command failed")
        
        agent = TesterAgent(llm=None)
        state = AgentState(
            jira_ticket_id="DP-123",
            repo_path="/tmp/project",
        )
        
        result = agent.run(state)
        
        assert result.test_results["success"] is False
        assert "error" in result.test_results
    
    @patch("src.agents.tester.run_command")
    def test_truncates_long_output(self, mock_run_command):
        long_output = "x" * 5000
        mock_run_command.invoke.return_value = {
            "success": True,
            "stdout": long_output,
            "stderr": "",
        }
        
        agent = TesterAgent(llm=None)
        state = AgentState(
            jira_ticket_id="DP-123",
            repo_path="/tmp/project",
        )
        
        result = agent.run(state)
        
        assert len(result.test_results["output"]) <= 2000
    
    @patch("src.agents.tester.run_command")
    def test_generates_summary(self, mock_run_command):
        mock_run_command.invoke.return_value = {
            "success": True,
            "stdout": "Tests: 7 passed, 3 failed",
            "stderr": "",
        }
        
        agent = TesterAgent(llm=None)
        state = AgentState(
            jira_ticket_id="DP-123",
            repo_path="/tmp/project",
        )
        
        result = agent.run(state)
        
        assert result.test_results["summary"] == "7 passed, 3 failed"
