from datetime import timedelta
from typing import Optional

from redis import asyncio as aioredis
from pydantic import BaseModel


redis_client: aioredis.Redis = None  # type: ignore


class RedisSchema(BaseModel):
    key: bytes | str
    value: bytes | str
    ttl: Optional[int | timedelta]


async def set_key(redis_data: RedisSchema, is_transaction: bool = False) -> None:
    async with redis_client.pipeline(transaction=is_transaction) as pipe:
        await pipe.set(redis_data.key, redis_data.value)
        if redis_data.ttl:
            await pipe.expire(redis_data.key, redis_data.ttl)

        await pipe.execute()


async def get_by_key(key: str) -> Optional[str]:
    return await redis_client.get(key)


async def delete_by_key(key: str) -> None:
    return await redis_client.delete(key)
