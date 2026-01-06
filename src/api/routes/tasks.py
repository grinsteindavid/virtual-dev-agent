"""Task management endpoints."""

from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from src.logger import get_logger
from src.agents.graph import create_dev_workflow

router = APIRouter()
logger = get_logger(__name__)

tasks_store: dict = {}


class TaskCreate(BaseModel):
    """Request model for creating a task."""
    jira_ticket_id: str


class TaskResponse(BaseModel):
    """Response model for task status."""
    task_id: str
    jira_ticket_id: str
    status: str
    pr_url: Optional[str] = None
    error: Optional[str] = None


def run_workflow(task_id: str, jira_ticket_id: str):
    """Background task to run the workflow."""
    logger.info(f"Starting workflow for task {task_id}, ticket {jira_ticket_id}")
    
    try:
        graph = create_dev_workflow()
        result = graph.invoke({
            "jira_ticket_id": jira_ticket_id,
            "status": "pending",
        })
        
        tasks_store[task_id] = {
            "task_id": task_id,
            "jira_ticket_id": jira_ticket_id,
            "status": result.get("status", "unknown"),
            "pr_url": result.get("pr_url"),
            "error": result.get("error"),
        }
        logger.info(f"Workflow completed for task {task_id}: {result.get('status')}")
        
    except Exception as e:
        logger.error(f"Workflow failed for task {task_id}: {e}")
        tasks_store[task_id] = {
            "task_id": task_id,
            "jira_ticket_id": jira_ticket_id,
            "status": "failed",
            "error": str(e),
        }


@router.post("", status_code=201, response_model=TaskResponse)
def create_task(task: TaskCreate, background_tasks: BackgroundTasks):
    """Create a new task to process a Jira ticket."""
    task_id = str(uuid4())
    
    tasks_store[task_id] = {
        "task_id": task_id,
        "jira_ticket_id": task.jira_ticket_id,
        "status": "pending",
        "pr_url": None,
        "error": None,
    }
    
    background_tasks.add_task(run_workflow, task_id, task.jira_ticket_id)
    
    logger.info(f"Created task {task_id} for ticket {task.jira_ticket_id}")
    return tasks_store[task_id]


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str):
    """Get the status of a task."""
    if task_id not in tasks_store:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks_store[task_id]


@router.get("", response_model=list[TaskResponse])
def list_tasks():
    """List all tasks."""
    return list(tasks_store.values())
