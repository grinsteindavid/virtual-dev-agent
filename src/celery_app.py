"""Celery application configuration."""

from celery import Celery

from src.config import config

celery_app = Celery(
    "virtual_dev",
    broker=config.redis.url,
    backend=config.redis.url,
    include=["src.tasks.workflow"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3300,
    worker_prefetch_multiplier=1,
    worker_concurrency=2,
    result_expires=86400,
)
