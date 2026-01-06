"""Fixtures for e2e tests."""

import os
import time

import httpx
import pytest


E2E_API_URL = os.getenv("E2E_API_URL", "http://localhost:5000")
E2E_TIMEOUT = int(os.getenv("E2E_TIMEOUT", "300"))


def is_e2e_enabled() -> bool:
    """Check if e2e tests should run."""
    return os.getenv("RUN_E2E_TESTS", "").lower() in ("1", "true", "yes")


pytestmark = pytest.mark.skipif(
    not is_e2e_enabled(),
    reason="E2E tests require RUN_E2E_TESTS=1 and running services"
)


@pytest.fixture(scope="session")
def api_url() -> str:
    """Base URL for API."""
    return E2E_API_URL


@pytest.fixture
def api_client(api_url: str) -> httpx.Client:
    """HTTP client for API requests."""
    with httpx.Client(base_url=api_url, timeout=30) as client:
        yield client


@pytest.fixture
def wait_for_task(api_client: httpx.Client):
    """Fixture to poll task status until completion."""
    def _wait(task_id: str, timeout: int = E2E_TIMEOUT) -> dict:
        start = time.time()
        while time.time() - start < timeout:
            response = api_client.get(f"/tasks/{task_id}")
            data = response.json()
            
            if data["status"] in ("done", "failed", "SUCCESS", "FAILED"):
                return data
            
            time.sleep(2)
        
        raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")
    
    return _wait


@pytest.fixture
def test_jira_ticket() -> str:
    """Jira ticket ID for e2e testing."""
    ticket = os.getenv("E2E_JIRA_TICKET")
    if not ticket:
        pytest.skip("E2E_JIRA_TICKET not set")
    return ticket
