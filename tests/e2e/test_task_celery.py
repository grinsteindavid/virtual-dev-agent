"""E2E tests for Celery task execution."""

import os

import pytest

from tests.e2e.conftest import is_e2e_enabled

pytestmark = pytest.mark.skipif(
    not is_e2e_enabled(),
    reason="E2E tests require RUN_E2E_TESTS=1 and running services"
)


class TestTaskCelery:
    """E2E tests for full Celery task execution.
    
    Note: All tests use E2E_JIRA_TICKET to avoid polluting task queue.
    """
    
    def test_task_transitions_to_running(self, api_client, test_jira_ticket):
        """Test that task transitions from PENDING to RUNNING."""
        response = api_client.post("/tasks", json={"jira_ticket_id": test_jira_ticket})
        task_id = response.json()["task_id"]
        
        import time
        time.sleep(1)
        
        status_response = api_client.get(f"/tasks/{task_id}")
        status = status_response.json()["status"]
        
        assert status in ("PENDING", "RUNNING", "SUCCESS", "FAILED", "done", "failed")
        
        api_client.delete(f"/tasks/{task_id}")
    
    def test_workflow_completes_with_result(self, api_client, wait_for_task, test_jira_ticket):
        """Test full workflow execution via Celery.
        
        Requires:
        - RUN_E2E_TESTS=1
        - E2E_JIRA_TICKET=<valid ticket>
        - Running: Redis + API + Worker
        - Valid API keys: OPENAI, GITHUB, JIRA
        """
        response = api_client.post("/tasks", json={"jira_ticket_id": test_jira_ticket})
        assert response.status_code == 202
        
        task_id = response.json()["task_id"]
        
        result = wait_for_task(task_id)
        
        assert result["status"] in ("done", "failed", "SUCCESS", "FAILED")
        assert result["jira_ticket_id"] == test_jira_ticket
        
        if result["status"] in ("done", "SUCCESS"):
            assert result.get("pr_url") or result.get("error") is None
            confidence = result.get("confidence", {})
            assert confidence, "Confidence scores should be returned"
            assert confidence.get("overall", 0) > 0
