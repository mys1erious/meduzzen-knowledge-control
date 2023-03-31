# I will rework this file later, approach with asyncio.run() doesnt work when deployed
# ..........................

import asyncio
import datetime
import json
import csv
import os

from fastapi.responses import StreamingResponse
from async_generator import async_generator

from app.core.exceptions import BadRequestException
from app.logging import file_logger
from app.database import get_redis
from app.quizzes.schemas import AttemptRedisSchema
from app.quizzes.services import quiz_service
from app.users.services import user_service


class FORMAT_TYPES:
    JSON = 'json'
    CSV = 'csv'


MEDIA_TYPES = {
    FORMAT_TYPES.JSON: 'application/json',
    FORMAT_TYPES.CSV: 'text/csv'
}


class ExportService:
    # def __init__(self):
    #     self.redis = None
    #     asyncio.run(self.init_async())
    #     # try:
    #     #     asyncio.run(self.init_async())
    #     # except RuntimeError:
    #     #     pass
    #
    # async def init_async(self):
    #     self.redis = await get_redis()

    async def export_my_results(self, current_user_id: int, format: str, filename: str = None) -> StreamingResponse:
        # data = self.redis.scan_iter(f'*user_id:{current_user_id}*')
        redis = await get_redis()
        data = redis.scan_iter(f'*user_id:{current_user_id}*')
        results = await self.get_results_from_iter_data(data)
        return await export_service.export_file(
            data=results,
            filename=filename,
            format=format
        )

    async def export_company_user_results(
            self,
            current_user_id: int,
            format: str,
            company_id: int,
            user_id: int = None,
            filename: str = None
    ) -> StreamingResponse:
        await user_service.user_company_is_admin(
            user_id=current_user_id,
            company_id=company_id
        )

        key = f'*company_id:{company_id}*'
        if user_id:
            await user_service.user_company_is_member(
                user_id=user_id,
                company_id=company_id
            )
            key = f'*user_id:{user_id}-{key.replace("*", "")}*'

        redis = await get_redis()
        data = redis.scan_iter(key)
        results = await self.get_results_from_iter_data(data)
        return await export_service.export_file(
            data=results,
            format=format,
            filename=filename
        )

    async def export_quiz_results(
            self,
            current_user_id: int,
            format: str,
            quiz_id: int,
            filename: str = None
    ) -> StreamingResponse:
        company_id = await quiz_service.get_company_id_by_quiz_id(quiz_id)
        await user_service.user_company_is_admin(
            user_id=current_user_id,
            company_id=company_id
        )
        redis = await get_redis()
        data = redis.scan_iter(f'*quiz_id:{quiz_id}*')
        results = await self.get_results_from_iter_data(data)
        return await export_service.export_file(
            data=results,
            format=format,
            filename=filename
        )

    async def export_file(
            self,
            format: str,
            data: list[AttemptRedisSchema],
            filename: str = None
    ) -> StreamingResponse:
        if not filename:
            now = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
            filename = f'results_{now}.{format.lower()}'

        res = await self.stream_file_response(data=data, format=format, filename=filename)
        self.clean_on_response_sent(filename)
        return res

    async def stream_file_response(
            self,
            format: str,
            data: list[AttemptRedisSchema],
            filename: str
    ) -> StreamingResponse:
        if format == FORMAT_TYPES.CSV:
            self.create_csv_file(data=data, filename=filename)
        elif format == FORMAT_TYPES.JSON:
            self.create_json_file(data=data, filename=filename)
        else:
            raise BadRequestException(f'Wrong format provided: {format}')

        file = open(filename, mode='rb')
        return StreamingResponse(
            file,
            media_type=MEDIA_TYPES[format],
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )

    def clean_on_response_sent(self, filename: str) -> None:
        try:
            os.remove(filename)
        except OSError as e:
            file_logger.error(f'clean_on_response_sent error --> {e}')

    def create_csv_file(self, data: list[AttemptRedisSchema], filename: str) -> None:
        csv_header = list(data[0].dict().keys())
        with open(filename, mode='w', newline='') as csv_file:
            writer = csv.writer(csv_file, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow(csv_header)
            for d in data:
                writer.writerow(d.dict().values())

    def create_json_file(self, data: list[AttemptRedisSchema], filename: str = None) -> None:
        with open(filename, mode='w', newline='') as json_file:
            json.dump([d.dict() for d in data], json_file, indent=4)

    async def get_results_from_iter_data(self, iter_data: async_generator) -> list[AttemptRedisSchema]:
        results = []
        redis = await get_redis()
        async for key in iter_data:
            hash_value = await redis.hgetall(key)
            results.append(AttemptRedisSchema(**{
                key.decode('utf-8'): json.loads(value.decode('utf-8'))
                for key, value in hash_value.items()
            }))
        return results


export_service = ExportService()
