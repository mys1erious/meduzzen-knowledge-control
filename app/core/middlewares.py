import json
from fastapi import Request, Response
from starlette.background import BackgroundTask

from app.logging import file_logger


WRITE_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']


def log_info(request: Request, response_body: bytes, status_code: int):
    json_body = json.dumps(json.loads(response_body), indent=2)
    url_path = str(request.url).replace(str(request.base_url), "")
    msg = f'"{request.method}" Request to "{url_path}" Returned:\n' \
          f'{json_body}\n' \
          f'with status code "{status_code}".'
    file_logger.info(msg)


async def log_writes_middleware(request: Request, call_next):
    response = await call_next(request)

    if request.method in WRITE_METHODS:
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        log_task = BackgroundTask(log_info, request, response_body, response.status_code)

        return Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
            background=log_task
        )

    return response
