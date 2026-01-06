"""E2E tests for /tasks API endpoints."""

import pytest

from tests.e2e.conftest import is_e2e_enabled

pytestmark = pytest.mark.skipif(
    not is_e2e_enabled(),
    reason="E2E tests require RUN_E2E_TESTS=1 and running services"
)


class TestTaskEndpoints:
    """E2E tests for task API endpoints with real Redis/Celery.
    
    Note: These tests create tasks then immediately cancel them
    to avoid running actual workflows with test ticket IDs.
    """
    
    def test_post_tasks_returns_202(self, api_client, test_jira_ticket):
        """Test POST /tasks returns 202 with task_id."""
        response = api_client.post("/tasks", json={"jira_ticket_id": test_jira_ticket})
        
        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data
        assert data["jira_ticket_id"] == test_jira_ticket
        assert data["status"] == "PENDING"
        
        api_client.delete(f"/tasks/{data['task_id']}")
    
    def test_get_task_returns_status(self, api_client, test_jira_ticket):
        """Test GET /tasks/{id} returns task status."""
        create_response = api_client.post("/tasks", json={"jira_ticket_id": test_jira_ticket})
        task_id = create_response.json()["task_id"]
        
        response = api_client.get(f"/tasks/{task_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] in ("PENDING", "RUNNING", "SUCCESS", "FAILED", "done", "failed")
        
        api_client.delete(f"/tasks/{task_id}")
    
    def test_get_nonexistent_task_returns_pending(self, api_client):
        """Test GET /tasks/{id} for unknown task returns PENDING."""
        response = api_client.get("/tasks/nonexistent-task-id-12345")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PENDING"
    
    def test_delete_task_returns_204(self, api_client, test_jira_ticket):
        """Test DELETE /tasks/{id} cancels task."""
        create_response = api_client.post("/tasks", json={"jira_ticket_id": test_jira_ticket})
        task_id = create_response.json()["task_id"]
        
        response = api_client.delete(f"/tasks/{task_id}")
        
        assert response.status_code == 204
    
    def test_post_tasks_invalid_payload_returns_422(self, api_client):
        """Test POST /tasks with invalid payload returns 422."""
        response = api_client.post("/tasks", json={"invalid": "payload"})
        
        assert response.status_code == 422
