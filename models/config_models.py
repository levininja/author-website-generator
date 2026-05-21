from enum import Enum
from typing import Optional
from pydantic import BaseModel


class ServerType(str, Enum):
    shared_standard = "shared_standard"
    ecommerce_demo = "ecommerce_demo"
    dedicated_ecommerce = "dedicated_ecommerce"


class ServerEntry(BaseModel):
    id: str
    name: str
    type: ServerType
    ip: str
    cloudways_server_id: str


class AppConfig(BaseModel):
    servers: list[ServerEntry]

    def get_server(self, server_id: str) -> Optional[ServerEntry]:
        return next((s for s in self.servers if s.id == server_id), None)
