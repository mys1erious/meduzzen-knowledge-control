from redis import asyncio as aioredis

from app.config import settings


async def get_redis():
    return await aioredis.from_url(settings.REDIS_URL)
