from typing import Literal

from fastapi import APIRouter, Depends
from fastapi_utils.cbv import cbv
from fastapi.responses import StreamingResponse

from app.core.exceptions import ForbiddenException, ForbiddenHTTPException, NotFoundException, NotFoundHTTPException, \
    BadRequestException, BadRequestHTTPException
from app.users.dependencies import get_current_user
from app.users.schemas import UserResponse

from app.export.services import export_service


router = APIRouter(tags=['Export Redis Data'])


@cbv(router)
class ExportCBV:
    current_user: UserResponse = Depends(get_current_user)
    format: Literal['json', 'csv'] = 'json'
    filename: str = None

    @router.get('/my-results/')
    async def export_my_results(self):
        try:
            return await export_service.export_my_results(
                current_user_id=self.current_user.user_id,
                filename=self.filename,
                format=self.format
            )
        except BadRequestException as e:
            raise BadRequestHTTPException(str(e))

    @router.get('/company-results/{company_id}/', response_class=StreamingResponse)
    async def export_company_user_results(self, company_id: int, user_id: int = None) -> StreamingResponse:
        try:
            return await export_service.export_company_user_results(
                current_user_id=self.current_user.user_id,
                filename=self.filename,
                format=self.format,
                company_id=company_id,
                user_id=user_id,
            )
        except ForbiddenException as e:
            raise ForbiddenHTTPException(str(e))
        except BadRequestException as e:
            raise BadRequestHTTPException(str(e))

    @router.get('/quiz-results/{quiz_id}/', response_class=StreamingResponse)
    async def export_quiz_results(self, quiz_id: int) -> StreamingResponse:
        try:
            return await export_service.export_quiz_results(
                current_user_id=self.current_user.user_id,
                filename=self.filename,
                format=self.format,
                quiz_id=quiz_id
            )
        except ForbiddenException as e:
            raise ForbiddenHTTPException(str(e))
        except NotFoundException as e:
            raise NotFoundHTTPException(str(e))
        except BadRequestException as e:
            raise BadRequestHTTPException(str(e))
