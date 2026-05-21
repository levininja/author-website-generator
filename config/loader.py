import os
import yaml
from pydantic import ValidationError

from models.config_models import AppConfig


class ConfigError(Exception):
    pass


def load_config(path: str) -> AppConfig:
    """Load and validate config.yaml. Raises ConfigError on any problem."""
    _assert_required_env_vars()

    if not os.path.exists(path):
        raise ConfigError(f"Config file not found: {path}")

    with open(path) as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict) or "servers" not in raw:
        raise ConfigError("config.yaml must contain a top-level 'servers' key")

    try:
        return AppConfig(**raw)
    except ValidationError as exc:
        raise ConfigError(f"Config validation failed: {exc}") from exc


def _assert_required_env_vars() -> None:
    missing = [v for v in ("ADMIN_USERNAME", "ADMIN_PASSWORD") if not os.environ.get(v)]
    if missing:
        raise ConfigError(
            f"Required environment variable(s) not set: {', '.join(missing)}. "
            "Set them before starting the application."
        )
