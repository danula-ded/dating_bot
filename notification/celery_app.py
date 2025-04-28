"""Celery application configuration."""
from celery import Celery
import logging

from notification.storage.db import engine, async_session
from notification.storage.models import User, Profile
from config.settings import settings

# Create Celery app
celery_app = Celery('notification')
celery_app.config_from_object('notification.celeryconfig')

# Import tasks after configuring the app
from notification.tasks import check_likes  # noqa

# Register tasks
celery_app.tasks.register(check_likes) 