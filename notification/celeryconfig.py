from datetime import timedelta

# Broker settings
broker_url = 'redis://redis:6379/0'
result_backend = 'redis://redis:6379/0'

# Task settings
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True

# Beat schedule
beat_schedule = {
    'check-likes-every-2-minutes': {
        'task': 'notification.tasks.check_likes',
        'schedule': 120.0,  # 2 minutes
        'options': {'expires': 110},  # Task expires after 110 seconds
    },
}

# Worker settings
task_soft_time_limit = 300
task_time_limit = 600
worker_prefetch_multiplier = 1
task_acks_late = True
task_reject_on_worker_lost = True

# Result backend settings
result_expires = 60
task_ignore_result = True
task_store_errors_even_if_ignored = False

# Broker transport options
broker_transport_options = {
    'visibility_timeout': 3600,
    'fanout_prefix': True,
    'fanout_patterns': True,
}
