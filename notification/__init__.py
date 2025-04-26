"""Notification service package."""
from notification.celery_app import celery_app
from notification.register_tasks import *  # This will register all tasks

__all__ = ['celery_app']  