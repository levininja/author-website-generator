"""Tests for config/loader.py — all tests run against in-memory YAML strings, no disk I/O."""

import textwrap

import pytest

from config.loader import ConfigError, load_config

VALID_YAML = textwrap.dedent("""\
    website_servers:
      - id: shared-standard
        name: Shared Non-Ecommerce Server
        type: standard
        ip: 1.2.3.4
        cloudways_server_id: cw-server-abc123
      - id: ecommerce-demo
        name: Ecommerce Demo Server
        type: ecommerce
        ip: 5.6.7.8
        cloudways_server_id: cw-server-def456
""")


def test_valid_config_returns_app_config(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(VALID_YAML)
    config = load_config(str(cfg_file))
    assert len(config.website_servers) == 2
    assert config.website_servers[0].id == "shared-standard"
    assert config.website_servers[0].ip == "1.2.3.4"
    assert config.website_servers[1].type.value == "ecommerce"


def test_server_lookup_by_id(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(VALID_YAML)
    config = load_config(str(cfg_file))
    server = config.get_server("shared-standard")
    assert server.name == "Shared Non-Ecommerce Server"


def test_get_server_returns_none_for_unknown_id(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(VALID_YAML)
    config = load_config(str(cfg_file))
    assert config.get_server("nonexistent") is None


def test_raises_on_missing_servers_key(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("some_other_key: value\n")
    with pytest.raises(ConfigError):
        load_config(str(cfg_file))


def test_raises_on_invalid_server_type(tmp_path):
    bad_yaml = textwrap.dedent("""\
        website_servers:
          - id: bad-server
            name: Bad Server
            type: not_a_valid_type
            ip: 1.2.3.4
    """)
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(bad_yaml)
    with pytest.raises(ConfigError):
        load_config(str(cfg_file))


def test_raises_on_server_missing_ip(tmp_path):
    bad_yaml = textwrap.dedent("""\
        website_servers:
          - id: no-ip
            name: No IP Server
            type: standard
    """)
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(bad_yaml)
    with pytest.raises(ConfigError):
        load_config(str(cfg_file))


def test_raises_if_config_file_missing():
    with pytest.raises(ConfigError, match="not found"):
        load_config("/nonexistent/path/config.yaml")
