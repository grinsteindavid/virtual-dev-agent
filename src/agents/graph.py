"""LangGraph workflow for Virtual Developer Agent."""

from typing import Literal

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from src.config import config
from src.logger import get_logger
from src.db.checkpointer import get_checkpointer
from src.agents.state import GraphState, AgentState, default_confidence
from src.agents.supervisor import SupervisorAgent
from src.agents.planner import PlannerAgent
from src.agents.implementer import ImplementerAgent
from src.agents.tester import TesterAgent
from src.agents.reporter import ReporterAgent

logger = get_logger(__name__)


def calc_overall_confidence(confidence: dict) -> float:
    """Calculate weighted overall confidence."""
    weights = {
        "routing": 0.1,
        "planning": 0.2,
        "implementation": 0.3,
        "testing": 0.4,
    }
    total = sum(confidence.get(k, 0) * v for k, v in weights.items())
    return round(total, 3)


def create_dev_workflow(llm=None, checkpointer=None, use_checkpointer=True):
    """Create the virtual developer multi-agent workflow graph.
    
    Args:
        llm: Language model to use. Defaults to OpenAI if configured.
        checkpointer: Custom checkpointer. If None and use_checkpointer=True, uses Redis.
        use_checkpointer: Whether to use checkpointing. Defaults to True.
    """
    if checkpointer is None and use_checkpointer:
        checkpointer = get_checkpointer()
    
    if llm is None and config.llm.openai_api_key:
        llm = ChatOpenAI(
            model=config.llm.model,
            api_key=config.llm.openai_api_key,
            temperature=0,
        )
    
    supervisor = SupervisorAgent(llm=llm)
    planner = PlannerAgent(llm=llm)
    implementer = ImplementerAgent(llm=llm)
    tester = TesterAgent(llm=llm)
    reporter = ReporterAgent(llm=llm)
    
    def supervisor_node(state: GraphState) -> dict:
        """Supervisor node - routes to next agent."""
        agent_state = AgentState.from_graph_state(state)
        result = supervisor.route(agent_state)
        return {
            "route": result.route,
            "confidence": result.confidence,
        }
    
    def planner_node(state: GraphState) -> dict:
        """Planner node - fetches Jira and creates plan."""
        agent_state = AgentState.from_graph_state(state)
        result = planner.run(agent_state)
        conf = {**state.get("confidence", default_confidence()), **result.confidence}
        conf["overall"] = calc_overall_confidence(conf)
        return {
            "jira_details": result.jira_details,
            "branch_name": result.branch_name,
            "implementation_plan": result.implementation_plan,
            "status": result.status,
            "error": result.error,
            "confidence": conf,
        }
    
    def implementer_node(state: GraphState) -> dict:
        """Implementer node - writes code."""
        agent_state = AgentState.from_graph_state(state)
        result = implementer.run(agent_state)
        conf = {**state.get("confidence", default_confidence()), **result.confidence}
        conf["overall"] = calc_overall_confidence(conf)
        return {
            "repo_path": result.repo_path,
            "code_changes": result.code_changes,
            "status": result.status,
            "error": result.error,
            "confidence": conf,
        }
    
    def tester_node(state: GraphState) -> dict:
        """Tester node - runs tests."""
        agent_state = AgentState.from_graph_state(state)
        result = tester.run(agent_state)
        conf = {**state.get("confidence", default_confidence()), **result.confidence}
        conf["overall"] = calc_overall_confidence(conf)
        return {
            "test_results": result.test_results,
            "test_iterations": result.test_iterations,
            "status": result.status,
            "error": result.error,
            "confidence": conf,
        }
    
    def reporter_node(state: GraphState) -> dict:
        """Reporter node - creates PR and notifications."""
        agent_state = AgentState.from_graph_state(state)
        result = reporter.run(agent_state)
        conf = {**state.get("confidence", default_confidence()), **result.confidence}
        conf["overall"] = calc_overall_confidence(conf)
        return {
            "pr_url": result.pr_url,
            "pr_number": result.pr_number,
            "status": result.status,
            "error": result.error,
            "confidence": conf,
        }
    
    def route_decision(state: GraphState) -> Literal["planner", "implementer", "tester", "reporter", "__end__"]:
        """Route to next node based on supervisor decision."""
        route = state.get("route", "planner")
        if route == "done":
            return "__end__"
        if state.get("status") == "failed":
            return "__end__"
        return route
    
    graph = StateGraph(GraphState)
    
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("planner", planner_node)
    graph.add_node("implementer", implementer_node)
    graph.add_node("tester", tester_node)
    graph.add_node("reporter", reporter_node)
    
    graph.set_entry_point("supervisor")
    
    graph.add_conditional_edges(
        "supervisor",
        route_decision,
        {
            "planner": "planner",
            "implementer": "implementer",
            "tester": "tester",
            "reporter": "reporter",
            "__end__": END,
        },
    )
    
    graph.add_edge("planner", "supervisor")
    graph.add_edge("implementer", "supervisor")
    graph.add_edge("tester", "supervisor")
    graph.add_edge("reporter", "supervisor")
    
    if checkpointer:
        logger.info("Compiling graph with checkpointer")
        return graph.compile(checkpointer=checkpointer)
    
    return graph.compile()
