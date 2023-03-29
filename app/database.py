from redis import asyncio as aioredis
import databases
from app.config import settings


# I couldn't make it work with your setup through the dependency override in the conftest.py
#   I tried making another container in docker for db, it didn't help
#   and a lot of other stuff...
# This approach is the one that worked for me, its basically the same as yours with get_db override,
#   but it checks whether the ENVIRONMENT variable is 'SETTINGS'
#   and if it is, it immediately creates a test db that cancels the need to override get_db,
#   ENVIRONMENT variable is defined in the pyproject.toml under the [tool.pytest.ini_options],
#   so whenever you run 'pytest' it will always use test db
if settings.ENVIRONMENT.is_testing:
    database = databases.Database(settings.POSTGRES_URL_TEST, force_rollback=True)
else:
    database = databases.Database(settings.POSTGRES_URL)


def get_db() -> databases.Database:
    return database


async def get_redis():
    if settings.ENVIRONMENT.is_testing:
        return await aioredis.from_url(settings.REDIS_URL_TEST)
    else:
        return await aioredis.from_url(settings.REDIS_URL)
