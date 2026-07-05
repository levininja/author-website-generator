"""Tests for Django project configuration."""

import json
import os
import subprocess
import sys

from django.conf import settings
from django.apps import apps


def test_staticfiles_app_is_installed_for_development_asset_serving():
    assert apps.is_installed("django.contrib.staticfiles")


def test_local_uploads_use_the_ignored_media_directory():
    assert settings.MEDIA_ROOT.name == "media"
    assert settings.MEDIA_URL == "/media/"
    assert settings.STORAGES["default"]["BACKEND"] == (
        "django.core.files.storage.FileSystemStorage"
    )


def test_r2_environment_selects_s3_storage_and_the_cdn_domain():
    environment = {
        **os.environ,
        "R2_ACCOUNT_ID": "account-id",
        "R2_ACCESS_KEY_ID": "access-key",
        "R2_SECRET_ACCESS_KEY": "secret-key",
        "R2_BUCKET_NAME": "awg-media",
        "R2_CUSTOM_DOMAIN": "media.example.com",
    }
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import json; "
                "from generator import settings; "
                "print(json.dumps(settings.STORAGES['default']))"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )

    storage = json.loads(result.stdout)
    assert storage["BACKEND"] == "storages.backends.s3.S3Storage"
    assert storage["OPTIONS"]["bucket_name"] == "awg-media"
    assert storage["OPTIONS"]["custom_domain"] == "media.example.com"
    assert storage["OPTIONS"]["endpoint_url"] == (
        "https://account-id.r2.cloudflarestorage.com"
    )
