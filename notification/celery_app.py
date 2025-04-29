"""Celery application configuration."""
from celery import Celery
import logging

from notification.storage.db import engine, async_session
from notification.storage.models import User, Profile
from config.settings import settings

celery_app = Celery('notification')
celery_app.config_from_object('notification.celeryconfig')

from notification.tasks import check_likes  # noqa

celery_app.tasks.register(check_likes)
