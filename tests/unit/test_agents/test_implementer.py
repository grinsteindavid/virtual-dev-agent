"""Tests for ImplementerAgent."""

import pytest
from unittest.mock import patch, MagicMock

from src.agents.state import AgentState
from src.agents.implementer import ImplementerAgent
from tests.mocks.mock_llm import FakeLLM


class TestImplementerAgent:
    """Tests for implementer agent."""
    
    @patch("src.tools.filesystem.run_command")
    def test_run_without_llm_uses_placeholder(self, mock_run_command):
        mock_run_command.invoke.return_value = {"success": True, "stdout": "", "stderr": ""}
        
        agent = ImplementerAgent(llm=None)
        state = AgentState(
            jira_ticket_id="DP-123",
            jira_details={"fields": {"summary": "Test feature"}},
            branch_name="DP-123",
            implementation_plan="1. Create component",
        )
        
        result = agent.run(state)
        
        assert result.code_changes
        assert result.code_changes[0]["file"] == "src/components/Feature.jsx"
        assert result.status == "implementing"
    
    @patch("src.tools.filesystem.run_command")
    def test_run_with_llm_generates_code(self, mock_run_command):
        mock_run_command.invoke.return_value = {"success": True, "stdout": "", "stderr": ""}
        
        llm_response = """Here's the implementation:

File: src/components/Greeting.jsx
```jsx
import React from 'react';
const Greeting = () => <h1>Hello</h1>;
export default Greeting;
```
"""
        fake_llm = FakeLLM(response=llm_response)
        agent = ImplementerAgent(llm=fake_llm)
        state = AgentState(
            jira_ticket_id="DP-123",
            jira_details={"fields": {"summary": "Create greeting"}},
            branch_name="DP-123",
            implementation_plan="1. Create Greeting component",
        )
        
        result = agent.run(state)
        
        assert len(fake_llm.calls) == 1
        assert result.status == "implementing"
        assert result.confidence["implementation"] == 0.7
    
    @patch("src.tools.filesystem.run_command")
    def test_clone_failure_sets_error(self, mock_run_command):
        mock_run_command.invoke.return_value = {
            "success": False,
            "stdout": "",
            "stderr": "fatal: repository not found",
        }
        
        agent = ImplementerAgent(llm=None)
        state = AgentState(
            jira_ticket_id="DP-123",
            jira_details={"fields": {"summary": "Test"}},
            branch_name="DP-123",
        )
        
        result = agent.run(state)
        
        assert result.status == "failed"
        assert "Repository setup failed" in result.error
    
    def test_parse_code_response_extracts_files(self):
        agent = ImplementerAgent(llm=None)
        content = """Here's the code:

File: src/utils/helper.js
```javascript
export const helper = () => 'hello';
```

File: src/components/Widget.jsx
```jsx
import React from 'react';
export default () => <div>Widget</div>;
```
"""
        changes = agent._parse_code_response(content)
        
        assert len(changes) >= 1
        assert any("helper" in c.get("content", "") for c in changes)
    
    def test_parse_code_response_handles_empty_content(self):
        agent = ImplementerAgent(llm=None)
        changes = agent._parse_code_response("")
        
        assert changes
        assert changes[0]["file"] == "src/components/Feature.jsx"
    
    def test_placeholder_implementation_structure(self):
        agent = ImplementerAgent(llm=None)
        state = AgentState(jira_ticket_id="DP-123")
        
        changes = agent._placeholder_implementation(state)
        
        assert len(changes) == 1
        assert changes[0]["file"] == "src/components/Feature.jsx"
        assert changes[0]["action"] == "create"
        assert "React" in changes[0]["content"]
        assert "PropTypes" in changes[0]["content"]
    
    @patch("src.tools.filesystem.run_command")
    @patch("src.tools.filesystem.write_file")
    def test_write_files_called_for_each_change(self, mock_write, mock_run_command):
        mock_run_command.invoke.return_value = {"success": True, "stdout": "", "stderr": ""}
        mock_write.invoke.return_value = {"success": True}
        
        agent = ImplementerAgent(llm=None)
        state = AgentState(
            jira_ticket_id="DP-123",
            jira_details={"fields": {"summary": "Test"}},
            branch_name="DP-123",
            implementation_plan="plan",
        )
        
        agent.run(state)
        
        assert mock_write.invoke.called
    
    @patch("src.tools.filesystem.run_command")
    def test_run_handles_exception(self, mock_run_command):
        mock_run_command.invoke.side_effect = Exception("Unexpected error")
        
        agent = ImplementerAgent(llm=None)
        state = AgentState(
            jira_ticket_id="DP-123",
            jira_details={"fields": {"summary": "Test"}},
            branch_name="DP-123",
        )
        
        result = agent.run(state)
        
        assert result.status == "failed"
        assert "Implementer error" in result.error
    
    @patch("src.tools.filesystem.run_command")
    def test_sets_repo_path_in_state(self, mock_run_command):
        mock_run_command.invoke.return_value = {"success": True, "stdout": "", "stderr": ""}
        
        agent = ImplementerAgent(llm=None)
        state = AgentState(
            jira_ticket_id="DP-123",
            jira_details={"fields": {"summary": "Test"}},
            branch_name="DP-123",
        )
        
        result = agent.run(state)
        
        assert result.repo_path
        assert "DP-123" in result.repo_path
