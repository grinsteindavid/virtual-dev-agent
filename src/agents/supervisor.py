"""Supervisor agent for routing workflow."""

import json
import re

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage

from src.agents.state import AgentState
from src.logger import get_logger

logger = get_logger(__name__)


ROUTING_PROMPT = """You are a routing agent for a virtual developer workflow system.

Analyze the current state and decide which agent should handle the next step:

- **planner**: Initial planning - fetch Jira ticket details and create implementation plan
  - Use when: status is "pending" or no implementation plan exists
  
- **implementer**: Code implementation - clone repo, create branch, write code
  - Use when: implementation plan exists but no code changes yet
  - Also use when: tests failed and fix_suggestions exist (implementer will use them)
  
- **tester**: Run tests
  - Use when: code changes exist but tests haven't run yet
  - Use when: skip_implementation is True (existing code needs testing)
  
- **reporter**: Create PR, update Jira, notify Discord
  - Use when: tests have passed successfully
  
- **done**: Workflow complete
  - Use when: PR has been created and Jira updated

Current state:
- Jira Ticket: {jira_ticket_id}
- Status: {status}
- Has Jira Details: {has_jira_details}
- Has Implementation Plan: {has_plan}
- Has Code Changes: {has_code_changes}
- Skip Implementation: {skip_implementation}
- Test Results: {test_results}
- Test Iterations: {test_iterations}
- Has Fix Suggestions: {has_fix_suggestions}
- Has PR URL: {has_pr_url}
- Error: {error}

Respond with JSON only: {{"route": "planner|implementer|tester|reporter|done", "confidence": 0.0-1.0, "reason": "brief explanation"}}"""


class SupervisorAgent:
    """Routes workflow to appropriate specialist agents."""
    
    MAX_TEST_ITERATIONS = 3
    
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
    
    def route(self, state: AgentState) -> AgentState:
        """Determine which agent should handle the next step."""
        logger.info(f"Routing: ticket={state.jira_ticket_id}, status={state.status}")
        
        test_passed = state.test_results.get("success", False) if state.test_results else False
        
        prompt = ROUTING_PROMPT.format(
            jira_ticket_id=state.jira_ticket_id or "(none)",
            status=state.status,
            has_jira_details=bool(state.jira_details),
            has_plan=bool(state.implementation_plan),
            has_code_changes=bool(state.code_changes),
            skip_implementation=state.skip_implementation,
            test_results=f"passed={test_passed}, iterations={state.test_iterations}" if state.test_results else "not run",
            test_iterations=state.test_iterations,
            has_fix_suggestions=bool(state.fix_suggestions),
            has_pr_url=bool(state.pr_url),
            error=state.error or "(none)",
        )
        
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content="What should be the next step?"),
        ]
        
        response = self.llm.invoke(messages)
        content = response.content.strip()
        
        route, confidence, reason = self._parse_response(content, state)
        
        logger.info(f"Routed to: {route} (confidence: {confidence:.2f}) - {reason}")
        
        state.route = route
        state.confidence["routing"] = confidence
        return state
    
    def _parse_response(self, content: str, state: AgentState) -> tuple[str, float, str]:
        """Parse JSON response with route, confidence, and reason."""
        try:
            match = re.search(r'\{[^}]+\}', content, re.DOTALL)
            if match:
                data = json.loads(match.group())
                route = data.get("route", "").lower()
                confidence = float(data.get("confidence", 0.5))
                reason = data.get("reason", "")
            else:
                route = content.lower()
                confidence = 0.5
                reason = ""
        except (json.JSONDecodeError, ValueError):
            route = self._fallback_route(state)
            confidence = 0.3
            reason = "fallback routing"
        
        valid_routes = {"planner", "implementer", "tester", "reporter", "done"}
        if route not in valid_routes:
            logger.warning(f"Invalid route '{route}', using fallback")
            route = self._fallback_route(state)
            confidence = 0.3
            reason = "invalid route, using fallback"
        
        if route == "tester" and state.test_iterations >= self.MAX_TEST_ITERATIONS:
            logger.warning(f"Max test iterations ({self.MAX_TEST_ITERATIONS}) reached, routing to reporter")
            route = "reporter"
            reason = f"max test iterations reached ({self.MAX_TEST_ITERATIONS})"
        
        return route, min(max(confidence, 0.0), 1.0), reason
    
    def _fallback_route(self, state: AgentState) -> str:
        """Determine fallback route based on state."""
        if state.pr_url:
            return "done"
        if state.test_results and state.test_results.get("success"):
            return "reporter"
        if state.skip_implementation:
            return "tester"
        if state.test_results and not state.test_results.get("success") and state.fix_suggestions:
            return "implementer"
        if state.code_changes:
            return "tester"
        if state.implementation_plan:
            return "implementer"
        return "planner"
