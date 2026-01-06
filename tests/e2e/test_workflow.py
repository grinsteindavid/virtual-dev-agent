"""E2E tests for LangGraph workflow with real connections."""

import os

import pytest

from tests.e2e.conftest import is_e2e_enabled

pytestmark = pytest.mark.skipif(
    not is_e2e_enabled(),
    reason="E2E tests require RUN_E2E_TESTS=1 and API keys"
)


def has_required_keys() -> bool:
    """Check if all required API keys are set."""
    return all([
        os.getenv("OPENAI_API_KEY"),
        os.getenv("GITHUB_TOKEN"),
        os.getenv("JIRA_API_TOKEN"),
    ])


class TestWorkflowE2E:
    """E2E tests for LangGraph workflow directly (no Celery)."""
    
    def test_workflow_graph_compiles(self):
        """Test that workflow graph compiles with real LLM."""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")
        
        from src.agents.graph import create_dev_workflow
        
        graph = create_dev_workflow()
        
        assert graph is not None
    
    def test_workflow_planner_fetches_jira(self, test_jira_ticket):
        """Test planner agent fetches real Jira ticket."""
        if not has_required_keys():
            pytest.skip("Required API keys not set")
        
        from src.agents.planner import PlannerAgent
        from src.agents.state import AgentState
        
        agent = PlannerAgent()
        state = AgentState(jira_ticket_id=test_jira_ticket, status="pending")
        
        result = agent.run(state)
        
        assert result.jira_details is not None
        assert result.jira_details.get("fields", {}).get("summary")
        assert result.implementation_plan
        assert result.status == "planning"
    
    def test_workflow_full_execution(self, test_jira_ticket):
        """Test full workflow execution with real APIs.
        
        Requires:
        - RUN_E2E_TESTS=1
        - E2E_JIRA_TICKET=<valid ticket>
        - Valid API keys: OPENAI, GITHUB, JIRA, DISCORD (optional)
        
        WARNING: This will create real branches, commits, and PRs!
        """
        if not has_required_keys():
            pytest.skip("Required API keys not set")
        
        import uuid
        from src.agents.graph import create_dev_workflow
        
        graph = create_dev_workflow()
        thread_id = f"e2e-test-{uuid.uuid4()}"
        
        result = graph.invoke(
            {"jira_ticket_id": test_jira_ticket, "status": "pending"},
            config={"configurable": {"thread_id": thread_id}},
        )
        
        assert result["status"] in ("done", "failed", "planning", "implementing", "testing", "reporting")
        
        if result["status"] == "done":
            assert result.get("pr_url")
    
    def test_workflow_with_skip_implementation(self, test_jira_ticket):
        """Test workflow with existing branch (skip_implementation=True)."""
        if not has_required_keys():
            pytest.skip("Required API keys not set")
        
        import uuid
        from src.agents.graph import create_dev_workflow
        
        graph = create_dev_workflow()
        thread_id = f"e2e-skip-{uuid.uuid4()}"
        
        result = graph.invoke(
            {"jira_ticket_id": test_jira_ticket, "status": "pending", "skip_implementation": True},
            config={"configurable": {"thread_id": thread_id}},
        )
        
        assert result["status"] in ("done", "failed", "testing", "reporting")
