"""Shared pytest fixtures for Virtual Developer Agent tests."""

import pytest

from tests.mocks.mock_llm import FakeLLM
from tests.mocks.mock_github import MockGitHubClient, MOCK_PR, MOCK_REPO
from tests.mocks.mock_jira import MockJiraClient, MOCK_ISSUE, MOCK_TRANSITIONS
from tests.mocks.mock_discord import MockDiscordClient


@pytest.fixture
def fake_llm():
    """Provide a fake LLM that returns predefined responses."""
    return FakeLLM()


@pytest.fixture
def routing_llm_planner():
    """Fake LLM that routes to planner."""
    return FakeLLM(response='{"route": "planner", "confidence": 0.9, "reason": "no plan yet"}')


@pytest.fixture
def routing_llm_implementer():
    """Fake LLM that routes to implementer."""
    return FakeLLM(response='{"route": "implementer", "confidence": 0.9, "reason": "plan exists"}')


@pytest.fixture
def routing_llm_tester():
    """Fake LLM that routes to tester."""
    return FakeLLM(response='{"route": "tester", "confidence": 0.9, "reason": "code exists"}')


@pytest.fixture
def routing_llm_reporter():
    """Fake LLM that routes to reporter."""
    return FakeLLM(response='{"route": "reporter", "confidence": 0.9, "reason": "tests passed"}')


@pytest.fixture
def routing_llm_done():
    """Fake LLM that routes to done."""
    return FakeLLM(response='{"route": "done", "confidence": 1.0, "reason": "PR created"}')


@pytest.fixture
def mock_github():
    """Provide mock GitHub client."""
    return MockGitHubClient()


@pytest.fixture
def mock_jira():
    """Provide mock Jira client."""
    return MockJiraClient()


@pytest.fixture
def mock_discord():
    """Provide mock Discord client."""
    return MockDiscordClient()


@pytest.fixture
def sample_ticket_id():
    """Sample Jira ticket ID."""
    return "DP-123"


@pytest.fixture
def sample_graph_state():
    """Sample initial graph state."""
    return {
        "jira_ticket_id": "DP-123",
        "status": "pending",
    }


@pytest.fixture
def sample_graph_state_with_plan():
    """Sample graph state with plan."""
    return {
        "jira_ticket_id": "DP-123",
        "jira_details": MOCK_ISSUE,
        "branch_name": "DP-123",
        "implementation_plan": "1. Create component\n2. Add tests",
        "status": "planning",
    }


@pytest.fixture
def sample_graph_state_with_code():
    """Sample graph state with code changes."""
    return {
        "jira_ticket_id": "DP-123",
        "jira_details": MOCK_ISSUE,
        "branch_name": "DP-123",
        "implementation_plan": "1. Create component\n2. Add tests",
        "repo_path": "/tmp/project_DP-123",
        "code_changes": [
            {"file": "src/components/Greeting.jsx", "content": "...", "action": "create"}
        ],
        "status": "implementing",
    }


@pytest.fixture
def sample_graph_state_tests_passed():
    """Sample graph state with passing tests."""
    return {
        "jira_ticket_id": "DP-123",
        "jira_details": MOCK_ISSUE,
        "branch_name": "DP-123",
        "implementation_plan": "1. Create component\n2. Add tests",
        "repo_path": "/tmp/project_DP-123",
        "code_changes": [
            {"file": "src/components/Greeting.jsx", "content": "...", "action": "create"}
        ],
        "test_results": {"success": True, "passed": 5, "failed": 0},
        "test_iterations": 1,
        "status": "testing",
    }
