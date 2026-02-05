from typing import Optional

from pydantic import BaseModel, Field


class EdgePCConfig(BaseModel):
    host: str = Field(..., min_length=1)
    port: int = 22
    username: str = Field(..., min_length=1)


class MSSQLConfig(BaseModel):
    enabled: bool = False
    host: str = ""
    port: int = 1433
    username: str = ""
    password: Optional[str] = None
    database: str = "HISTORISCH"
    table: str = "Tab_Actual"
    poll_interval_seconds: int = 60
    window_minutes: int = 10
    max_rows_per_poll: int = 5000


class ConnectionsRead(BaseModel):
    edge_pc: Optional[EdgePCConfig] = None
    mssql: MSSQLConfig


class ConnectionsUpdate(BaseModel):
    edge_pc: Optional[EdgePCConfig] = None
    mssql: Optional[MSSQLConfig] = None


class MSSQLTestRequest(BaseModel):
    config: Optional[MSSQLConfig] = None


class MSSQLTestResponse(BaseModel):
    ok: bool
    message: str
