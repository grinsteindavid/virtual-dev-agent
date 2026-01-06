"""State definitions for LangGraph workflow."""

from dataclasses import dataclass, field
from typing import Literal, TypedDict


def default_confidence() -> dict:
    """Default confidence scores."""
    return {
        "routing": 0.0,
        "planning": 0.0,
        "implementation": 0.0,
        "testing": 0.0,
        "overall": 0.0,
    }


RouteType = Literal["planner", "implementer", "tester", "reporter", "done"]
StatusType = Literal["pending", "planning", "implementing", "testing", "reporting", "done", "failed"]


class GraphState(TypedDict, total=False):
    """LangGraph state definition using TypedDict."""
    
    jira_ticket_id: str
    jira_details: dict
    branch_name: str
    implementation_plan: str
    repo_path: str
    code_changes: list[dict]
    test_results: dict
    test_iterations: int
    fix_suggestions: str
    branch_exists: bool
    existing_context: dict
    skip_implementation: bool
    pr_url: str
    pr_number: int
    route: RouteType | None
    status: StatusType
    error: str | None
    confidence: dict


@dataclass
class AgentState:
    """Dataclass for agent internal processing."""
    
    jira_ticket_id: str = ""
    jira_details: dict = field(default_factory=dict)
    branch_name: str = ""
    implementation_plan: str = ""
    repo_path: str = ""
    code_changes: list[dict] = field(default_factory=list)
    test_results: dict = field(default_factory=dict)
    test_iterations: int = 0
    fix_suggestions: str = ""
    branch_exists: bool = False
    existing_context: dict = field(default_factory=dict)
    skip_implementation: bool = False
    pr_url: str = ""
    pr_number: int = 0
    route: RouteType | None = None
    status: StatusType = "pending"
    error: str | None = None
    confidence: dict = field(default_factory=default_confidence)
    
    @classmethod
    def from_graph_state(cls, state: dict) -> "AgentState":
        """Create AgentState from LangGraph state dict."""
        return cls(
            jira_ticket_id=state.get("jira_ticket_id", ""),
            jira_details=state.get("jira_details", {}),
            branch_name=state.get("branch_name", ""),
            implementation_plan=state.get("implementation_plan", ""),
            repo_path=state.get("repo_path", ""),
            code_changes=state.get("code_changes", []),
            test_results=state.get("test_results", {}),
            test_iterations=state.get("test_iterations", 0),
            fix_suggestions=state.get("fix_suggestions", ""),
            branch_exists=state.get("branch_exists", False),
            existing_context=state.get("existing_context", {}),
            skip_implementation=state.get("skip_implementation", False),
            pr_url=state.get("pr_url", ""),
            pr_number=state.get("pr_number", 0),
            route=state.get("route"),
            status=state.get("status", "pending"),
            error=state.get("error"),
            confidence=state.get("confidence", default_confidence()),
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for graph state update."""
        return {
            "jira_ticket_id": self.jira_ticket_id,
            "jira_details": self.jira_details,
            "branch_name": self.branch_name,
            "implementation_plan": self.implementation_plan,
            "repo_path": self.repo_path,
            "code_changes": self.code_changes,
            "test_results": self.test_results,
            "test_iterations": self.test_iterations,
            "fix_suggestions": self.fix_suggestions,
            "branch_exists": self.branch_exists,
            "existing_context": self.existing_context,
            "skip_implementation": self.skip_implementation,
            "pr_url": self.pr_url,
            "pr_number": self.pr_number,
            "route": self.route,
            "status": self.status,
            "error": self.error,
            "confidence": self.confidence,
        }
