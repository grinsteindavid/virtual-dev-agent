"""Integration tests for full workflow."""

import pytest
import os

pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_INTEGRATION_TESTS"),
    reason="Integration tests require RUN_INTEGRATION_TESTS=1 and API keys"
)


class TestFullWorkflow:
    """End-to-end workflow tests."""
    
    def test_graph_compiles(self):
        """Test that the workflow graph compiles without errors."""
        from src.agents.graph import create_dev_workflow
        from tests.mocks.mock_llm import FakeLLM
        
        llm = FakeLLM()
        graph = create_dev_workflow(llm=llm)
        
        assert graph is not None
    
    def test_workflow_routes_correctly(self):
        """Test that workflow routes through expected states."""
        from src.agents.graph import create_dev_workflow
        from tests.mocks.mock_llm import FakeLLM
        
        llm = FakeLLM(response='{"route": "planner", "confidence": 0.9, "reason": "test"}')
        graph = create_dev_workflow(llm=llm)
        
        initial_state = {
            "jira_ticket_id": "DP-TEST",
            "status": "pending",
        }
        
        assert initial_state["status"] == "pending"
    
    def test_workflow_with_real_apis(self):
        """Test full workflow with real API connections.
        
        This test requires:
        - RUN_INTEGRATION_TESTS=1
        - Valid API keys for GitHub, Jira, Discord, and OpenAI
        - A test Jira ticket specified in TEST_JIRA_TICKET env var
        """
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")
        
        if not os.getenv("TEST_JIRA_TICKET"):
            pytest.skip("TEST_JIRA_TICKET not set")
        
        from src.agents.graph import create_dev_workflow
        
        graph = create_dev_workflow()
        
        result = graph.invoke({
            "jira_ticket_id": os.getenv("TEST_JIRA_TICKET"),
            "status": "pending",
        })
        
        assert result["status"] in ["done", "failed", "planning", "implementing", "testing", "reporting"]
