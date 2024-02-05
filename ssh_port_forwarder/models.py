from pydantic import BaseModel


class Connection(BaseModel):
    id: str
    name: str
    host: str
    ssh_port: int = 22
    description: str | None = None
    ports: list[int]
    enabled: bool = False
