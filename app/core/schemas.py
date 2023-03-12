from datetime import datetime

from pydantic import BaseModel


class HealthCheckSchema(BaseModel):
    status_code: int = 200
    detail: str = 'ok'
    result: str = 'working'


class TimeStampSchema(BaseModel):
    created_at: datetime
    updated_at: datetime


class DetailResponse(BaseModel):
    detail: str
