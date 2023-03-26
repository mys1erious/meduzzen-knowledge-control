from datetime import datetime

from pydantic import BaseModel


def root_validator_round_floats(values: dict, precision: int = 3) -> dict:
    for field, value in values.items():
        if isinstance(value, float):
            values[field] = round(value, precision)
    return values


class HealthCheckSchema(BaseModel):
    status_code: int = 200
    detail: str = 'ok'
    result: str = 'working'


class TimeStampSchema(BaseModel):
    created_at: datetime
    updated_at: datetime


class DetailResponse(BaseModel):
    detail: str
