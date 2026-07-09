import os

import yaml
from pydantic import ValidationError

from models.config_models import AppConfig


class ConfigError(Exception):
    """Raised when application configuration cannot be loaded."""

    pass


def load_config(path: str) -> AppConfig:
    """Load and validate the YAML application configuration."""
    if not os.path.exists(path):
        raise ConfigError(f"Config file not found: {path}")

    with open(path) as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict) or "website_servers" not in raw:
        raise ConfigError("config.yaml must contain a top-level 'website_servers' key")

    try:
        return AppConfig(**raw)
    except ValidationError as exc:
        raise ConfigError(f"Config validation failed: {exc}") from exc
