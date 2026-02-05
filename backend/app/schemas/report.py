from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


class ReportRequest(BaseModel):
    format: Literal["csv", "pdf"] = "csv"
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    machine_id: Optional[str] = None
    sensor_id: Optional[str] = None


class ReportResponse(BaseModel):
    report_name: str
    url: str
    generated_at: datetime

