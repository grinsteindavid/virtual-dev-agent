"""Unit tests for workflow Celery task."""

import pytest
from unittest.mock import MagicMock, patch


class TestRunWorkflowTask:
    """Tests for run_workflow_task Celery task."""
    
    @patch("src.tasks.workflow.create_dev_workflow")
    def test_run_workflow_task_success(self, mock_create_workflow):
        """Test successful workflow execution."""
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = {
            "status": "done",
            "pr_url": "https://github.com/owner/repo/pull/123",
            "error": None,
        }
        mock_create_workflow.return_value = mock_graph
        
        from src.tasks.workflow import run_workflow_task
        
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"
        run_workflow_task.bind(mock_task)
        
        result = run_workflow_task.run("DP-123")
        
        assert result["jira_ticket_id"] == "DP-123"
        assert result["status"] == "done"
        assert result["pr_url"] == "https://github.com/owner/repo/pull/123"
        assert result["error"] is None
    
    @patch("src.tasks.workflow.create_dev_workflow")
    def test_run_workflow_task_failure(self, mock_create_workflow):
        """Test workflow execution with exception."""
        mock_create_workflow.side_effect = Exception("Workflow error")
        
        from src.tasks.workflow import run_workflow_task
        
        result = run_workflow_task.run("DP-123")
        
        assert result["jira_ticket_id"] == "DP-123"
        assert result["status"] == "failed"
        assert "Workflow error" in result["error"]
    
    @patch("src.tasks.workflow.create_dev_workflow")
    def test_run_workflow_task_invokes_graph(self, mock_create_workflow):
        """Test that task invokes the workflow graph."""
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = {"status": "done"}
        mock_create_workflow.return_value = mock_graph
        
        from src.tasks.workflow import run_workflow_task
        
        run_workflow_task.run("DP-456")
        
        mock_graph.invoke.assert_called_once_with({
            "jira_ticket_id": "DP-456",
            "status": "pending",
        })
