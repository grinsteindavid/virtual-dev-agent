"""Celery tasks for AI workflow execution."""

from src.celery_app import celery_app
from src.agents.graph import create_dev_workflow
from src.logger import get_logger

logger = get_logger(__name__)


@celery_app.task(bind=True, name="workflow.run")
def run_workflow_task(self, jira_ticket_id: str) -> dict:
    """Execute the AI development workflow for a Jira ticket.
    
    Args:
        jira_ticket_id: The Jira ticket ID to process
        
    Returns:
        dict with status, pr_url, error
    """
    task_id = getattr(self.request, 'id', None)
    logger.info(f"Starting workflow for ticket {jira_ticket_id}, task_id={task_id}")
    
    try:
        if task_id:
            self.update_state(state="RUNNING", meta={"jira_ticket_id": jira_ticket_id})
        
        graph = create_dev_workflow()
        thread_id = task_id or jira_ticket_id
        
        result = graph.invoke(
            {"jira_ticket_id": jira_ticket_id, "status": "pending"},
            config={"configurable": {"thread_id": thread_id}},
        )
        
        logger.info(f"Workflow completed for {jira_ticket_id}: {result.get('status')}")
        
        return {
            "jira_ticket_id": jira_ticket_id,
            "status": result.get("status", "unknown"),
            "pr_url": result.get("pr_url"),
            "error": result.get("error"),
        }
        
    except Exception as e:
        logger.error(f"Workflow failed for {jira_ticket_id}: {e}")
        return {
            "jira_ticket_id": jira_ticket_id,
            "status": "failed",
            "error": str(e),
        }
