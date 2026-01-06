"""Planner agent for fetching Jira details and creating implementation plans."""

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage

from src.agents.state import AgentState
from src.clients.jira_client import JiraClient, get_jira_client
from src.logger import get_logger

logger = get_logger(__name__)


PLANNING_PROMPT = """You are a software development planner. Based on the Jira ticket details below, create a concise implementation plan.

Jira Ticket: {ticket_key}
Summary: {summary}
Description: {description}
Status: {status}
Priority: {priority}
{comments_section}
Create a step-by-step implementation plan that includes:
1. What components/files need to be created or modified
2. Key implementation details
3. Test cases to write
4. Any edge cases to consider

Keep the plan concise and actionable. Focus on the essential steps.
If there are comments with additional requirements or clarifications, incorporate them into the plan."""


class PlannerAgent:
    """Fetches Jira ticket details and creates implementation plans."""
    
    def __init__(self, jira_client: JiraClient = None, llm: BaseChatModel = None):
        self.jira_client = jira_client
        self.llm = llm
    
    def _get_jira_client(self) -> JiraClient:
        """Get Jira client, using injected or singleton."""
        return self.jira_client or get_jira_client()
    
    def run(self, state: AgentState) -> AgentState:
        """Fetch Jira details and create implementation plan."""
        logger.info(f"Planner: processing ticket {state.jira_ticket_id}")
        
        try:
            jira = self._get_jira_client()
            issue = jira.get_issue(state.jira_ticket_id)
            comments = jira.get_comments(state.jira_ticket_id, limit=5)
            
            state.jira_details = issue
            state.jira_details["recent_comments"] = comments
            state.branch_name = state.jira_ticket_id
            
            fields = issue.get("fields", {})
            summary = fields.get("summary", "No summary")
            description = fields.get("description", "No description")
            status = fields.get("status", {}).get("name", "Unknown")
            priority = fields.get("priority", {}).get("name", "Medium") if fields.get("priority") else "Medium"
            
            if self.llm:
                plan = self._generate_plan(
                    ticket_key=state.jira_ticket_id,
                    summary=summary,
                    description=description,
                    status=status,
                    priority=priority,
                    comments=comments,
                )
            else:
                plan = self._default_plan(summary, description)
            
            state.implementation_plan = plan
            state.status = "planning"
            state.confidence["planning"] = 0.8
            
            logger.info(f"Planner: completed for {state.jira_ticket_id} with {len(comments)} comments")
            
        except Exception as e:
            logger.error(f"Planner error: {e}")
            state.error = f"Planner error: {str(e)}"
            state.status = "failed"
        
        return state
    
    def _format_comments(self, comments: list[dict]) -> str:
        """Format comments for inclusion in prompt."""
        if not comments:
            return ""
        lines = ["\nRecent Comments (newest first):"]
        for c in comments:
            author = c.get("author", "Unknown")
            body = c.get("body", "")[:300]
            lines.append(f"- {author}: {body}")
        return "\n".join(lines) + "\n"
    
    def _generate_plan(
        self,
        ticket_key: str,
        summary: str,
        description: str,
        status: str,
        priority: str,
        comments: list[dict] = None,
    ) -> str:
        """Generate implementation plan using LLM."""
        comments_section = self._format_comments(comments or [])
        
        prompt = PLANNING_PROMPT.format(
            ticket_key=ticket_key,
            summary=summary,
            description=description if description else "No description provided",
            status=status,
            priority=priority,
            comments_section=comments_section,
        )
        
        messages = [
            SystemMessage(content="You are a helpful software development assistant."),
            HumanMessage(content=prompt),
        ]
        
        response = self.llm.invoke(messages)
        return response.content.strip()
    
    def _default_plan(self, summary: str, description: str) -> str:
        """Create a default plan when no LLM is available."""
        return f"""Implementation Plan for: {summary}

1. Analyze requirements from description
2. Create necessary components/files
3. Implement core functionality
4. Write unit tests
5. Run tests and fix any failures
6. Commit and push changes

Description:
{description if description else 'No description provided'}
"""
