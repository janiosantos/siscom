"""
Celery Configuration - Tarefas Assíncronas e Webhooks
"""
from celery import Celery
from app.core.config import settings

# Configurar Celery
celery_app = Celery(
    "siscom",
    broker=settings.REDIS_URL or "redis://localhost:6379/1",
    backend=settings.REDIS_URL or "redis://localhost:6379/1"
)

# Configurações
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutos
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])
