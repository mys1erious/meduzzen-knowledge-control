import logging

import pytest
import asyncio
import pytest_asyncio

from typing import AsyncGenerator

from httpx import AsyncClient
from starlette.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.main import app
from app.config import settings as system_config
from app.database import database as test_db
from app.core.models import Base


engine_test = create_async_engine(system_config.POSTGRES_URL_TEST, poolclass=NullPool)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_app():
    client = TestClient(app)
    yield client


@pytest.fixture(autouse=True, scope='session')
async def prepare_database():
    await test_db.connect()
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await test_db.disconnect()
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="session")
async def ac() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope='session')
async def login_user(ac: AsyncClient, users_tokens):
    async def __send_request(user_email: str, user_password: str):
        payload = {
            "user_email": user_email,
            "user_password": user_password,
        }
        response = await ac.post("/users/sign-in/", data=payload)
        if response.status_code != 200:
            return response
        user_token = response.json().get('result').get('access_token')
        users_tokens[user_email] = user_token
        return response

    return __send_request


@pytest.fixture(scope='session')
def users_tokens():
    tokens_store = dict()
    return tokens_store
