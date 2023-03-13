import os
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.core.middlewares import log_writes_middleware
from app.database import get_db
from app.routes import router


# Build paths inside the project like this: os.path.join(BASE_DIR, 'subdir').
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(os.path.join(BASE_DIR, 'app'))


description = """
## Service for employee knowledge control.
This service will be useful for companies that need to control the knowledge of their employees.
    test results are recorded in a database, after which the analysis of the received data can be performed 
    and some actions taken against employees.
"""

app = FastAPI(
    title='Knowledge Control API',
    description=description,
    version=settings.APP_VERSION,
)


# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_headers=settings.CORS_HEADERS,
    allow_credentials=True,
    allow_methods=("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
)
# app.add_middleware(BaseHTTPMiddleware, dispatch=log_writes_middleware)


app.include_router(router)


# Events
@app.on_event('startup')
async def startup():
    await get_db().connect()


@app.on_event('shutdown')
async def shutdown():
    await get_db().disconnect()


def main():
    uvicorn.run(
        'app.main:app',
        reload=True,
        host=settings.HOST,
        port=settings.PORT
    )


if __name__ == '__main__':
    main()
