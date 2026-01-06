"""Task management endpoints using Celery."""

from typing import Optional

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.celery_app import celery_app
from src.tasks.workflow import run_workflow_task
from src.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


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


def _get_task_response(task_id: str) -> TaskResponse:
    """Build TaskResponse from Celery AsyncResult."""
    result = AsyncResult(task_id, app=celery_app)
    
    if result.state == "PENDING":
        return TaskResponse(
            task_id=task_id,
            jira_ticket_id="",
            status="PENDING",
        )
    
    if result.state == "RUNNING":
        meta = result.info or {}
        return TaskResponse(
            task_id=task_id,
            jira_ticket_id=meta.get("jira_ticket_id", ""),
            status="RUNNING",
        )
    
    if result.state == "SUCCESS":
        data = result.result or {}
        return TaskResponse(
            task_id=task_id,
            jira_ticket_id=data.get("jira_ticket_id", ""),
            status=data.get("status", "done"),
            pr_url=data.get("pr_url"),
            error=data.get("error"),
        )
    
    if result.state == "FAILURE":
        return TaskResponse(
            task_id=task_id,
            jira_ticket_id="",
            status="FAILED",
            error=str(result.info),
        )
    
    return TaskResponse(task_id=task_id, jira_ticket_id="", status=result.state)


@router.post("", status_code=202, response_model=TaskResponse)
def create_task(task: TaskCreate):
    """Submit a workflow task to the Celery queue."""
    result = run_workflow_task.delay(task.jira_ticket_id)
    logger.info(f"Queued task {result.id} for ticket {task.jira_ticket_id}")
    
    return TaskResponse(
        task_id=result.id,
        jira_ticket_id=task.jira_ticket_id,
        status="PENDING",
    )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str):
    """Get task status from Celery."""
    return _get_task_response(task_id)


@router.delete("/{task_id}", status_code=204)
def cancel_task(task_id: str):
    """Cancel a pending or running task."""
    celery_app.control.revoke(task_id, terminate=True)
    logger.info(f"Cancelled task {task_id}")
