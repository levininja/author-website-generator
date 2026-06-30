import yaml
from pydantic import ValidationError

from models.config_models import AppConfig
import os


class ConfigError(Exception):
    pass


def load_config(path: str) -> AppConfig:
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
