from celery import Celery

# Initialize Celery
celery_app = Celery('notification')

# Import tasks before configuring the app
from notification.tasks import check_likes  # noqa

# Configure the app
celery_app.config_from_object('notification.celeryconfig')

# Register tasks
celery_app.tasks.register(check_likes) 