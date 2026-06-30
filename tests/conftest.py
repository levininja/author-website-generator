import textwrap
import pytest


MINIMAL_CONFIG_YAML = textwrap.dedent("""\
    website_servers:
      - id: shared-standard
        name: Shared Non-Ecommerce Server
        type: standard
        ip: 1.2.3.4
        cloudways_server_id: cw-test-123
""")


@pytest.fixture
def config_file(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(MINIMAL_CONFIG_YAML)
    return str(cfg)
