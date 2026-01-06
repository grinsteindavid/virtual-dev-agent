# Testing Strategy

This document describes the testing approach for the LangGraph Virtual Developer Agent.

## Overview

Following the pattern from Clinical-Decision-Support-Multi-Agent-System:
- **Unit Tests**: No network calls, all dependencies mocked
- **Integration Tests**: Require API keys and services, test full workflow

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── mocks/
│   ├── __init__.py
│   ├── mock_llm.py          # FakeLLM class
│   ├── mock_github.py       # MockGitHubClient + fixtures
│   ├── mock_jira.py         # MockJiraClient + fixtures
│   └── mock_discord.py      # MockDiscordClient
├── unit/
│   ├── test_config.py
│   ├── test_clients/
│   │   ├── test_github_client.py
│   │   ├── test_jira_client.py
│   │   └── test_discord_client.py
│   ├── test_tools/
│   │   ├── test_github_tools.py
│   │   ├── test_jira_tools.py
│   │   ├── test_discord_tools.py
│   │   └── test_filesystem_tools.py
│   └── test_agents/
│       ├── test_supervisor.py
│       ├── test_planner.py
│       ├── test_implementer.py
│       ├── test_tester.py
│       ├── test_reporter.py
│       └── test_graph.py
└── integration/
    ├── test_api_health.py
    ├── test_api_tasks.py
    └── test_full_workflow.py
```

---

## Mock Implementations

### FakeLLM (`tests/mocks/mock_llm.py`)

```python
from langchain_core.messages import AIMessage

class FakeLLM:
    """Fake LLM for unit tests - no API calls."""
    
    def __init__(self, response: str = "Test response"):
        self.response = response
        self.calls = []
    
    def invoke(self, messages):
        self.calls.append(messages)
        return AIMessage(content=self.response)
    
    async def ainvoke(self, messages):
        return self.invoke(messages)
```

### MockGitHubClient (`tests/mocks/mock_github.py`)

```python
MOCK_REPO = {
    "full_name": "owner/repo",
    "description": "Test repository",
    "language": "JavaScript",
    "stargazers_count": 10,
    "html_url": "https://github.com/owner/repo"
}

MOCK_PR = {
    "number": 42,
    "title": "feat: implement DP-123",
    "state": "open",
    "html_url": "https://github.com/owner/repo/pull/42",
    "head": {"ref": "DP-123"},
    "base": {"ref": "main"}
}

class MockGitHubClient:
    """Mock GitHub client - no network calls."""
    
    def __init__(self):
        self.calls = []
    
    def get_repo(self, owner: str, repo: str) -> dict:
        self.calls.append(("get_repo", owner, repo))
        return MOCK_REPO
    
    def create_pull_request(self, owner: str, repo: str, title: str, body: str, head: str, base: str) -> dict:
        self.calls.append(("create_pull_request", owner, repo, title, head, base))
        return MOCK_PR
    
    def create_pr_comment(self, owner: str, repo: str, pr_number: int, body: str) -> dict:
        self.calls.append(("create_pr_comment", owner, repo, pr_number))
        return {"id": 12345, "html_url": f"https://github.com/{owner}/{repo}/pull/{pr_number}#issuecomment-12345"}
    
    def list_pull_requests(self, owner: str, repo: str, state: str = "open", limit: int = 10) -> list[dict]:
        self.calls.append(("list_pull_requests", owner, repo, state, limit))
        return [MOCK_PR]
```

### MockJiraClient (`tests/mocks/mock_jira.py`)

```python
MOCK_ISSUE = {
    "id": "10001",
    "key": "DP-123",
    "fields": {
        "summary": "Create greeting component",
        "description": "Implement a Greeting component that displays personalized messages",
        "status": {"name": "In Progress"},
        "assignee": {"displayName": "Developer"},
        "priority": {"name": "Medium"},
        "created": "2024-01-01T00:00:00.000Z",
        "updated": "2024-01-02T00:00:00.000Z",
        "attachment": [],
        "comment": {"comments": []}
    }
}

MOCK_TRANSITIONS = [
    {"id": "21", "name": "In Review", "to": {"name": "In Review"}},
    {"id": "31", "name": "Done", "to": {"name": "Done"}}
]

class MockJiraClient:
    """Mock Jira client - no network calls."""
    
    def __init__(self):
        self.calls = []
    
    def get_issue(self, issue_key: str) -> dict:
        self.calls.append(("get_issue", issue_key))
        return {**MOCK_ISSUE, "key": issue_key}
    
    def list_issues(self, status: str = "To Do", limit: int = 10) -> list[dict]:
        self.calls.append(("list_issues", status, limit))
        return [MOCK_ISSUE]
    
    def add_comment(self, issue_key: str, comment: str) -> dict:
        self.calls.append(("add_comment", issue_key, comment))
        return {"id": "10001"}
    
    def get_transitions(self, issue_key: str) -> list[dict]:
        self.calls.append(("get_transitions", issue_key))
        return MOCK_TRANSITIONS
    
    def transition_issue(self, issue_key: str, transition_id: str) -> dict:
        self.calls.append(("transition_issue", issue_key, transition_id))
        return {"success": True}
```

### MockDiscordClient (`tests/mocks/mock_discord.py`)

```python
class MockDiscordClient:
    """Mock Discord client - no network calls."""
    
    def __init__(self):
        self.calls = []
    
    def send_message(self, content: str, username: str = None) -> dict:
        self.calls.append(("send_message", content, username))
        return {"success": True, "status": 204}
    
    def send_embed(self, title: str, description: str, color: int = None, url: str = None) -> dict:
        self.calls.append(("send_embed", title, description))
        return {"success": True, "status": 204}
    
    def send_notification(self, type: str, message: str, details: str = None) -> dict:
        self.calls.append(("send_notification", type, message))
        return {"success": True, "status": 204}
```

---

## Fixtures (`tests/conftest.py`)

```python
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
    return FakeLLM(response='{"route": "planner", "confidence": 0.9}')


@pytest.fixture
def routing_llm_implementer():
    """Fake LLM that routes to implementer."""
    return FakeLLM(response='{"route": "implementer", "confidence": 0.9}')


@pytest.fixture
def routing_llm_tester():
    """Fake LLM that routes to tester."""
    return FakeLLM(response='{"route": "tester", "confidence": 0.9}')


@pytest.fixture
def routing_llm_reporter():
    """Fake LLM that routes to reporter."""
    return FakeLLM(response='{"route": "reporter", "confidence": 0.9}')


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
        "status": "pending"
    }
```

---

## Unit Test Examples

### Supervisor Agent Tests

```python
# tests/unit/test_agents/test_supervisor.py

import pytest
from src.agents.state import AgentState
from src.agents.supervisor import SupervisorAgent
from tests.mocks.mock_llm import FakeLLM


class TestSupervisorAgent:
    
    def test_routes_to_planner_for_new_task(self):
        llm = FakeLLM(response='{"route": "planner", "confidence": 0.9}')
        supervisor = SupervisorAgent(llm=llm)
        
        state = AgentState(jira_ticket_id="DP-123", status="pending")
        result = supervisor.route(state)
        
        assert result.route == "planner"
        assert result.confidence["routing"] == 0.9
    
    def test_routes_to_implementer_after_planning(self):
        llm = FakeLLM(response='{"route": "implementer", "confidence": 0.85}')
        supervisor = SupervisorAgent(llm=llm)
        
        state = AgentState(
            jira_ticket_id="DP-123",
            implementation_plan="1. Create component\n2. Add tests",
            status="planning"
        )
        result = supervisor.route(state)
        
        assert result.route == "implementer"
    
    def test_routes_to_tester_after_implementation(self):
        llm = FakeLLM(response='{"route": "tester", "confidence": 0.9}')
        supervisor = SupervisorAgent(llm=llm)
        
        state = AgentState(
            jira_ticket_id="DP-123",
            code_changes=[{"file": "src/Greeting.jsx", "action": "create"}],
            status="implementing"
        )
        result = supervisor.route(state)
        
        assert result.route == "tester"
    
    def test_routes_to_reporter_when_tests_pass(self):
        llm = FakeLLM(response='{"route": "reporter", "confidence": 0.95}')
        supervisor = SupervisorAgent(llm=llm)
        
        state = AgentState(
            jira_ticket_id="DP-123",
            test_results={"passed": 5, "failed": 0, "success": True},
            status="testing"
        )
        result = supervisor.route(state)
        
        assert result.route == "reporter"
    
    def test_routes_to_done_after_reporting(self):
        llm = FakeLLM(response='{"route": "done", "confidence": 1.0}')
        supervisor = SupervisorAgent(llm=llm)
        
        state = AgentState(
            jira_ticket_id="DP-123",
            pr_url="https://github.com/owner/repo/pull/42",
            status="reporting"
        )
        result = supervisor.route(state)
        
        assert result.route == "done"
    
    def test_defaults_to_planner_on_invalid_route(self):
        llm = FakeLLM(response="invalid_response")
        supervisor = SupervisorAgent(llm=llm)
        
        state = AgentState(jira_ticket_id="DP-123")
        result = supervisor.route(state)
        
        assert result.route == "planner"
```

### Planner Agent Tests

```python
# tests/unit/test_agents/test_planner.py

import pytest
from src.agents.state import AgentState
from src.agents.planner import PlannerAgent
from tests.mocks.mock_llm import FakeLLM
from tests.mocks.mock_jira import MockJiraClient


class TestPlannerAgent:
    
    def test_fetches_jira_and_creates_plan(self):
        jira = MockJiraClient()
        llm = FakeLLM(response="1. Create Greeting component\n2. Add PropTypes\n3. Write tests")
        agent = PlannerAgent(jira_client=jira, llm=llm)
        
        state = AgentState(jira_ticket_id="DP-123")
        result = agent.run(state)
        
        assert "Create Greeting component" in result.implementation_plan
        assert ("get_issue", "DP-123") in jira.calls
    
    def test_sets_branch_name_from_ticket(self):
        jira = MockJiraClient()
        llm = FakeLLM()
        agent = PlannerAgent(jira_client=jira, llm=llm)
        
        state = AgentState(jira_ticket_id="DP-123")
        result = agent.run(state)
        
        assert result.branch_name == "DP-123"
    
    def test_includes_jira_details_in_state(self):
        jira = MockJiraClient()
        llm = FakeLLM()
        agent = PlannerAgent(jira_client=jira, llm=llm)
        
        state = AgentState(jira_ticket_id="DP-123")
        result = agent.run(state)
        
        assert result.jira_details["key"] == "DP-123"
        assert "summary" in result.jira_details["fields"]
```

### GitHub Tools Tests

```python
# tests/unit/test_tools/test_github_tools.py

import pytest
from unittest.mock import patch
from src.tools.github import create_pull_request, list_pull_requests
from tests.mocks.mock_github import MockGitHubClient, MOCK_PR


class TestGitHubTools:
    
    @patch("src.tools.github.get_github_client")
    def test_create_pull_request(self, mock_get_client):
        client = MockGitHubClient()
        mock_get_client.return_value = client
        
        result = create_pull_request.invoke({
            "owner": "owner",
            "repo": "repo",
            "title": "feat: DP-123",
            "body": "Implementation",
            "head": "DP-123",
            "base": "main"
        })
        
        assert result["number"] == 42
        assert result["html_url"] == MOCK_PR["html_url"]
        assert ("create_pull_request", "owner", "repo", "feat: DP-123", "DP-123", "main") in client.calls
    
    @patch("src.tools.github.get_github_client")
    def test_list_pull_requests(self, mock_get_client):
        client = MockGitHubClient()
        mock_get_client.return_value = client
        
        result = list_pull_requests.invoke({
            "owner": "owner",
            "repo": "repo",
            "state": "open",
            "limit": 5
        })
        
        assert len(result) == 1
        assert result[0]["number"] == 42
```

---

## Integration Test Examples

### API Health Tests

```python
# tests/integration/test_api_health.py

import pytest
from fastapi.testclient import TestClient
from src.api.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    
    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_health_includes_version(self, client):
        response = client.get("/health")
        assert "version" in response.json()
```

### Full Workflow Tests

```python
# tests/integration/test_full_workflow.py

import pytest
import os

pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_INTEGRATION_TESTS"),
    reason="Integration tests require RUN_INTEGRATION_TESTS=1"
)


class TestFullWorkflow:
    
    def test_workflow_completes_with_mock_ticket(self):
        """Test full workflow with a real API but test ticket."""
        from src.agents.graph import create_dev_workflow
        
        graph = create_dev_workflow()
        result = graph.invoke({
            "jira_ticket_id": os.getenv("TEST_JIRA_TICKET", "DP-TEST")
        })
        
        assert result["status"] in ["done", "failed"]
        if result["status"] == "done":
            assert result["pr_url"] is not None
```

---

## pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
log_cli = true
log_cli_level = INFO
addopts = -v --tb=short
markers =
    integration: marks tests as integration tests (require network/API keys)
```

---

## Makefile Commands

```makefile
.PHONY: test test-unit test-integration test-coverage

test-unit:
	pytest tests/unit -v

test-integration:
	RUN_INTEGRATION_TESTS=1 pytest tests/integration -v

test:
	pytest tests/unit -v

test-coverage:
	pytest tests/unit --cov=src --cov-report=term-missing --cov-report=html
```

---

## Test Execution Summary

| Command | Scope | Network | API Keys |
|---------|-------|---------|----------|
| `make test-unit` | Unit tests only | No | No |
| `make test-integration` | Integration tests | Yes | Yes |
| `make test` | Unit tests (default) | No | No |
| `make test-coverage` | Unit + coverage report | No | No |

---

## Important Notes

1. **No log mocking**: Per project requirements, tests must NOT mock logging. Use `jest.spyOn` pattern equivalent in pytest if asserting log calls.

2. **Fixture data**: Mock data should be realistic and match actual API responses.

3. **Skip markers**: Integration tests use `pytest.mark.skipif` to skip when `RUN_INTEGRATION_TESTS` is not set.

4. **Client injection**: Tools should accept clients via dependency injection or use `get_*_client()` factory functions that can be patched.
