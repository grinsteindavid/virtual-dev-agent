"""Tests for ImplementerAgent."""

import pytest
from unittest.mock import patch, MagicMock

from src.agents.state import AgentState
from src.agents.implementer import ImplementerAgent
from src.agents.parsers import parse_code_response
from tests.mocks.mock_llm import FakeLLM
from tests.mocks.mock_github import MockGitHubClient


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
    
    @patch("src.agents.implementer.clone_repo")
    def test_clone_failure_sets_error(self, mock_clone):
        mock_clone.invoke.return_value = {
            "success": False,
            "error": "fatal: repository not found",
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
        changes = parse_code_response(content)
        
        assert len(changes) >= 1
        assert any("helper" in c.get("content", "") for c in changes)
    
    def test_parse_code_response_handles_empty_content(self):
        changes = parse_code_response("")
        
        assert changes == []
    
    def test_placeholder_implementation_structure(self):
        agent = ImplementerAgent(llm=None)
        
        changes = agent._placeholder_implementation()
        
        assert len(changes) == 1
        assert changes[0]["file"] == "src/components/Feature.jsx"
        assert changes[0]["action"] == "create"
        assert "React" in changes[0]["content"]
        assert "PropTypes" in changes[0]["content"]
    
    @patch("src.agents.implementer.write_file")
    @patch("src.agents.implementer.run_command")
    @patch("src.agents.implementer.checkout_branch")
    @patch("src.agents.implementer.branch_exists_on_remote")
    @patch("src.agents.implementer.configure_git_user")
    @patch("src.agents.implementer.clone_repo")
    def test_write_files_called_for_each_change(self, mock_clone, mock_config, mock_branch_exists, mock_checkout, mock_run_command, mock_write):
        mock_clone.invoke.return_value = {"success": True}
        mock_branch_exists.invoke.return_value = False
        mock_checkout.invoke.return_value = {"success": True}
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
    
    @patch("src.agents.implementer.clone_repo")
    def test_run_handles_exception(self, mock_clone):
        mock_clone.invoke.side_effect = Exception("Unexpected error")
        
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


class TestImplementerBranchDetection:
    """Tests for branch detection and existing context."""
    
    @patch("src.agents.implementer.run_command")
    @patch("src.agents.implementer.checkout_branch")
    @patch("src.agents.implementer.branch_exists_on_remote")
    @patch("src.agents.implementer.configure_git_user")
    @patch("src.agents.implementer.clone_repo")
    def test_detects_existing_branch(self, mock_clone, mock_config, mock_branch_exists, mock_checkout, mock_run_command):
        mock_clone.invoke.return_value = {"success": True}
        mock_branch_exists.invoke.return_value = True
        mock_checkout.invoke.return_value = {"success": True}
        mock_run_command.invoke.return_value = {"success": True, "stdout": "", "stderr": ""}
        
        agent = ImplementerAgent(llm=None)
        result = agent._clone_and_setup("/tmp/test", "DP-123")
        
        assert result["success"]
        assert result["branch_exists"] is True
    
    @patch("src.agents.implementer.run_command")
    @patch("src.agents.implementer.checkout_branch")
    @patch("src.agents.implementer.branch_exists_on_remote")
    @patch("src.agents.implementer.configure_git_user")
    @patch("src.agents.implementer.clone_repo")
    def test_detects_new_branch(self, mock_clone, mock_config, mock_branch_exists, mock_checkout, mock_run_command):
        mock_clone.invoke.return_value = {"success": True}
        mock_branch_exists.invoke.return_value = False
        mock_checkout.invoke.return_value = {"success": True}
        mock_run_command.invoke.return_value = {"success": True, "stdout": "", "stderr": ""}
        
        agent = ImplementerAgent(llm=None)
        result = agent._clone_and_setup("/tmp/test", "DP-123")
        
        assert result["success"]
        assert result["branch_exists"] is False
    
    @patch("src.agents.implementer.run_command")
    @patch("src.agents.implementer.get_commit_log")
    @patch("src.agents.implementer.checkout_branch")
    @patch("src.agents.implementer.branch_exists_on_remote")
    @patch("src.agents.implementer.configure_git_user")
    @patch("src.agents.implementer.clone_repo")
    def test_skips_implementation_when_complete(self, mock_clone, mock_config, mock_branch_exists, mock_checkout, mock_get_log, mock_run_command):
        mock_clone.invoke.return_value = {"success": True}
        mock_branch_exists.invoke.return_value = True
        mock_checkout.invoke.return_value = {"success": True}
        mock_get_log.invoke.return_value = "abc123 feat: implement component"
        
        def run_side_effect(params):
            cmd = params.get("command", "")
            if "find src" in cmd:
                return {"success": True, "stdout": "src/Component.jsx", "stderr": ""}
            if "head -50" in cmd:
                return {"success": True, "stdout": "const Component = () => <div>Hello</div>;", "stderr": ""}
            return {"success": True, "stdout": "", "stderr": ""}
        
        mock_run_command.invoke.side_effect = run_side_effect
        
        llm = FakeLLM(response='{"complete": true, "reason": "Component implemented"}')
        github = MockGitHubClient()
        agent = ImplementerAgent(llm=llm, github_client=github)
        
        state = AgentState(
            jira_ticket_id="DP-123",
            jira_details={"fields": {"summary": "Create Component"}},
            branch_name="DP-123",
            implementation_plan="Create a component",
        )
        
        result = agent.run(state)
        
        assert result.skip_implementation is True
        assert result.branch_exists is True
        assert result.confidence["implementation"] == 0.9
    
    def test_build_context_section_includes_fix_suggestions(self):
        agent = ImplementerAgent(llm=None)
        state = AgentState(
            fix_suggestions="Fix the import statement",
            test_results={"output": "Error: cannot find module"},
        )
        
        context = agent._build_context_section(state)
        
        assert "Fix Suggestions" in context
        assert "Fix the import" in context
        assert "Test Failures" in context
    
    def test_build_context_section_includes_pr_comments(self):
        agent = ImplementerAgent(llm=None)
        state = AgentState(
            existing_context={
                "commits": "abc123 initial commit",
                "pr_comments": "- user: Please fix styling",
                "review_comments": "- reviewer on file.js: Add tests",
            }
        )
        
        context = agent._build_context_section(state)
        
        assert "Prior Commits" in context
        assert "PR Comments" in context
        assert "Please fix styling" in context
