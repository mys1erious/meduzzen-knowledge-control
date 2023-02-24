from fastapi import APIRouter

from app.logging import logger
from app.core.schemas import HealthCheckSchema

router = APIRouter(tags=['General'])


@router.get('/')
async def health_check() -> HealthCheckSchema:
    return HealthCheckSchema()
