from enum import Enum
from typing import Optional
from pydantic import BaseModel


class ServerType(str, Enum):
    standard = "standard"
    ecommerce = "ecommerce"


class WebsiteServer(BaseModel):
    id: str
    name: str
    type: ServerType
    ip: str
    cloudways_server_id: str


class AppConfig(BaseModel):
    website_servers: list[WebsiteServer]

    def get_server(self, server_id: str) -> Optional[WebsiteServer]:
        return next((s for s in self.website_servers if s.id == server_id), None)
