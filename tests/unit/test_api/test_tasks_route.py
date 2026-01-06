"""Unit tests for tasks API routes."""

import pytest
from unittest.mock import MagicMock, patch


class TestTasksRoute:
    """Tests for /tasks API endpoints."""
    
    @patch("src.api.routes.tasks.run_workflow_task")
    def test_create_task_returns_202(self, mock_task):
        """Test POST /tasks returns 202 Accepted."""
        from fastapi.testclient import TestClient
        from src.api.app import create_app
        
        mock_result = MagicMock()
        mock_result.id = "celery-task-id-123"
        mock_task.delay.return_value = mock_result
        
        app = create_app()
        client = TestClient(app)
        
        response = client.post("/tasks", json={"jira_ticket_id": "DP-123"})
        
        assert response.status_code == 202
        data = response.json()
        assert data["task_id"] == "celery-task-id-123"
        assert data["jira_ticket_id"] == "DP-123"
        assert data["status"] == "PENDING"
    
    @patch("src.api.routes.tasks.run_workflow_task")
    def test_create_task_calls_celery_delay(self, mock_task):
        """Test that create_task enqueues Celery task."""
        from fastapi.testclient import TestClient
        from src.api.app import create_app
        
        mock_result = MagicMock()
        mock_result.id = "test-id"
        mock_task.delay.return_value = mock_result
        
        app = create_app()
        client = TestClient(app)
        
        client.post("/tasks", json={"jira_ticket_id": "DP-456"})
        
        mock_task.delay.assert_called_once_with("DP-456")
    
    @patch("src.api.routes.tasks.AsyncResult")
    def test_get_task_pending(self, mock_async_result):
        """Test GET /tasks/{id} for pending task."""
        from fastapi.testclient import TestClient
        from src.api.app import create_app
        
        mock_result = MagicMock()
        mock_result.state = "PENDING"
        mock_async_result.return_value = mock_result
        
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/tasks/task-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task-123"
        assert data["status"] == "PENDING"
    
    @patch("src.api.routes.tasks.AsyncResult")
    def test_get_task_running(self, mock_async_result):
        """Test GET /tasks/{id} for running task."""
        from fastapi.testclient import TestClient
        from src.api.app import create_app
        
        mock_result = MagicMock()
        mock_result.state = "RUNNING"
        mock_result.info = {"jira_ticket_id": "DP-123"}
        mock_async_result.return_value = mock_result
        
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/tasks/task-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "RUNNING"
        assert data["jira_ticket_id"] == "DP-123"
    
    @patch("src.api.routes.tasks.AsyncResult")
    def test_get_task_success(self, mock_async_result):
        """Test GET /tasks/{id} for successful task."""
        from fastapi.testclient import TestClient
        from src.api.app import create_app
        
        mock_result = MagicMock()
        mock_result.state = "SUCCESS"
        mock_result.result = {
            "jira_ticket_id": "DP-123",
            "status": "done",
            "pr_url": "https://github.com/owner/repo/pull/1",
            "error": None,
        }
        mock_async_result.return_value = mock_result
        
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/tasks/task-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "done"
        assert data["pr_url"] == "https://github.com/owner/repo/pull/1"
    
    @patch("src.api.routes.tasks.AsyncResult")
    def test_get_task_failure(self, mock_async_result):
        """Test GET /tasks/{id} for failed task."""
        from fastapi.testclient import TestClient
        from src.api.app import create_app
        
        mock_result = MagicMock()
        mock_result.state = "FAILURE"
        mock_result.info = Exception("Task failed")
        mock_async_result.return_value = mock_result
        
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/tasks/task-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "FAILED"
        assert "Task failed" in data["error"]
    
    @patch("src.api.routes.tasks.celery_app")
    def test_cancel_task(self, mock_celery):
        """Test DELETE /tasks/{id} cancels task."""
        from fastapi.testclient import TestClient
        from src.api.app import create_app
        
        app = create_app()
        client = TestClient(app)
        
        response = client.delete("/tasks/task-123")
        
        assert response.status_code == 204
        mock_celery.control.revoke.assert_called_once_with("task-123", terminate=True)
