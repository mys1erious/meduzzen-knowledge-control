from redis import asyncio as aioredis
from app.config import settings


redis_client: aioredis.Redis = None  # type: ignore


async def redis_connect():
    pool = aioredis.ConnectionPool.from_url(
        settings.REDIS_URL,
        max_connections=10
    )
    return await aioredis.Redis(connection_pool=pool)
