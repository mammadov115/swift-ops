# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    "daphne",  # Must be first — replaces runserver with ASGI-aware server
    "unfold",  # Must be before django.contrib.admin
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # "django.contrib.humanize", # Handy template tags
    "django.contrib.admin",
    "django.contrib.gis",
    "django.forms",
]
THIRD_PARTY_APPS = [
    "channels",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_gis",
    "drf_spectacular",
    "django_filters",
    "django_extensions",
    "django_celery_beat",
]

LOCAL_APPS = [
    "apps.accounts",
    "apps.vehicles",
    "apps.tracking",
    "apps.zones",
    "apps.rides",
    "apps.payments",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS
