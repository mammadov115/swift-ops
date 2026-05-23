import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("swift_ops")

# Read configuration from Django settings, using the CELERY_ prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Automatically discover tasks in all INSTALLED_APPS.
app.autodiscover_tasks()
