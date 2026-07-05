import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-change-this-in-production")

DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() == "true"

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    "accounts",
    "onboarding",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "generator.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "generator.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

AUTH_USER_MODEL = "accounts.User"

STATIC_URL = "/static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(BASE_DIR) / "media"

R2_BUCKET_NAME = os.environ.get("R2_BUCKET_NAME", "")
if R2_BUCKET_NAME:
    R2_ACCOUNT_ID = os.environ["R2_ACCOUNT_ID"]
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "access_key": os.environ["R2_ACCESS_KEY_ID"],
                "secret_key": os.environ["R2_SECRET_ACCESS_KEY"],
                "bucket_name": R2_BUCKET_NAME,
                "endpoint_url": (
                    f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
                ),
                "custom_domain": os.environ["R2_CUSTOM_DOMAIN"],
                "default_acl": None,
                "querystring_auth": False,
                "file_overwrite": False,
            },
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
