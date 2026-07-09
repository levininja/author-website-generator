from enum import StrEnum

from pydantic import BaseModel


class ServerType(StrEnum):
    """Supported provisioning server categories."""

    standard = "standard"
    ecommerce = "ecommerce"


class WebsiteServer(BaseModel):
    """Configured Cloudways server available for generated sites."""

    id: str
    name: str
    type: ServerType
    ip: str
    cloudways_server_id: str


class AppConfig(BaseModel):
    """Validated application configuration loaded from YAML."""

    website_servers: list[WebsiteServer]

    def get_server(self, server_id: str) -> WebsiteServer | None:
        return next((s for s in self.website_servers if s.id == server_id), None)
