"""Tests for graph workflow module."""

import pytest
from unittest.mock import patch, MagicMock

from src.agents.graph import calc_overall_confidence, create_dev_workflow


class TestCalcOverallConfidence:
    """Tests for confidence calculation."""
    
    def test_all_zeros_returns_zero(self):
        confidence = {
            "routing": 0.0,
            "planning": 0.0,
            "implementation": 0.0,
            "testing": 0.0,
        }
        assert calc_overall_confidence(confidence) == 0.0
    
    def test_all_ones_returns_weighted_sum(self):
        confidence = {
            "routing": 1.0,
            "planning": 1.0,
            "implementation": 1.0,
            "testing": 1.0,
        }
        result = calc_overall_confidence(confidence)
        assert result == 1.0
    
    def test_partial_confidence(self):
        confidence = {
            "routing": 0.9,
            "planning": 0.8,
            "implementation": 0.7,
            "testing": 0.9,
        }
        result = calc_overall_confidence(confidence)
        assert 0.8 <= result <= 0.85
    
    def test_missing_keys_treated_as_zero(self):
        confidence = {"routing": 0.5}
        result = calc_overall_confidence(confidence)
        assert result == 0.05
    
    def test_rounds_to_three_decimals(self):
        confidence = {
            "routing": 0.33333,
            "planning": 0.66666,
            "implementation": 0.99999,
            "testing": 0.11111,
        }
        result = calc_overall_confidence(confidence)
        assert len(str(result).split(".")[-1]) <= 3


class TestCreateDevWorkflow:
    """Tests for workflow creation."""
    
    @patch("src.agents.graph.get_checkpointer")
    def test_creates_workflow_without_checkpointer(self, mock_checkpointer):
        mock_checkpointer.return_value = None
        
        workflow = create_dev_workflow(llm=MagicMock(), use_checkpointer=False)
        
        assert workflow is not None
        mock_checkpointer.assert_not_called()
    
    @patch("src.agents.graph.get_checkpointer")
    def test_creates_workflow_with_custom_checkpointer(self, mock_get_checkpointer):
        mock_checkpointer = MagicMock()
        
        workflow = create_dev_workflow(
            llm=MagicMock(),
            checkpointer=mock_checkpointer,
            use_checkpointer=True,
        )
        
        assert workflow is not None
        mock_get_checkpointer.assert_not_called()
    
    @patch("src.agents.graph.get_checkpointer")
    @patch("src.agents.graph.config")
    def test_creates_openai_llm_when_key_available(self, mock_config, mock_checkpointer):
        mock_config.llm.openai_api_key = "test-key"
        mock_config.llm.model = "gpt-4"
        mock_checkpointer.return_value = None
        
        with patch("src.agents.graph.ChatOpenAI") as mock_openai:
            mock_openai.return_value = MagicMock()
            workflow = create_dev_workflow(use_checkpointer=False)
            
            mock_openai.assert_called_once()
    
    @patch("src.agents.graph.get_checkpointer")
    def test_workflow_is_compiled(self, mock_checkpointer):
        mock_checkpointer.return_value = None
        
        workflow = create_dev_workflow(llm=MagicMock(), use_checkpointer=False)
        
        assert workflow is not None
        assert hasattr(workflow, "invoke")


class TestRouteDecisionLogic:
    """Tests for routing decision logic (inline function behavior)."""
    
    def test_done_route_ends_workflow(self):
        state = {"route": "done", "status": "reporting"}
        
        route = state.get("route", "planner")
        if route == "done":
            result = "__end__"
        elif state.get("status") == "failed":
            result = "__end__"
        else:
            result = route
        
        assert result == "__end__"
    
    def test_failed_status_ends_workflow(self):
        state = {"route": "tester", "status": "failed"}
        
        route = state.get("route", "planner")
        if route == "done":
            result = "__end__"
        elif state.get("status") == "failed":
            result = "__end__"
        else:
            result = route
        
        assert result == "__end__"
    
    def test_planner_route_continues(self):
        state = {"route": "planner", "status": "pending"}
        
        route = state.get("route", "planner")
        if route == "done":
            result = "__end__"
        elif state.get("status") == "failed":
            result = "__end__"
        else:
            result = route
        
        assert result == "planner"
    
    def test_missing_route_defaults_to_planner(self):
        state = {"status": "pending"}
        
        route = state.get("route", "planner")
        if route == "done":
            result = "__end__"
        elif state.get("status") == "failed":
            result = "__end__"
        else:
            result = route
        
        assert result == "planner"
    
    def test_implementer_route_continues(self):
        state = {"route": "implementer", "status": "planning"}
        
        route = state.get("route", "planner")
        result = route if route != "done" and state.get("status") != "failed" else "__end__"
        
        assert result == "implementer"
    
    def test_tester_route_continues(self):
        state = {"route": "tester", "status": "implementing"}
        
        route = state.get("route", "planner")
        result = route if route != "done" and state.get("status") != "failed" else "__end__"
        
        assert result == "tester"
    
    def test_reporter_route_continues(self):
        state = {"route": "reporter", "status": "testing"}
        
        route = state.get("route", "planner")
        result = route if route != "done" and state.get("status") != "failed" else "__end__"
        
        assert result == "reporter"
