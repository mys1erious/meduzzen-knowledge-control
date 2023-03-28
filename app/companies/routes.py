from fastapi import APIRouter, status, Depends
from fastapi.responses import JSONResponse
from fastapi_pagination import Page, Params
from fastapi_utils.cbv import cbv

from app.core.exceptions import ForbiddenHTTPException, NotFoundHTTPException
from app.core.utils import response_with_result_key
from app.core.pagination import paginate
from app.core.schemas import DetailResponse
from app.core.constants import SuccessDetails
from app.users.dependencies import get_current_user
from app.users.schemas import UserResponse, UserListResponse, AdminListResponse
from app.users.constants import ExceptionDetails as UserExceptionDetails
from app.users.exceptions import UserNotFoundException
from app.quizzes.schemas import QuizFullResponse
from app.quizzes.services import quiz_service

from .schemas import CompanyCreateRequest, CompanyResponse, CompanyListResponse, CompanyUpdateRequest, AddAdminRequest
from .services import company_service
from .exceptions import CompanyNotFoundException, NotYourCompanyException
from .constants import ExceptionDetails


base_router = APIRouter(tags=['Companies'])
action_router = APIRouter(tags=['Company Actions'])


@cbv(base_router)
class CompaniesCBV:
    current_user: UserResponse = Depends(get_current_user)

    @base_router.get('/', response_model=Page[CompanyResponse])
    async def get_companies(self, params: Params = Depends()) -> CompanyListResponse:
        companies = await company_service.get_companies(user_id=self.current_user.user_id)
        pagination = paginate(companies.companies, params, items_name='companies')
        return response_with_result_key(pagination)

    @base_router.post(
        '/',
        response_model=CompanyResponse,
        response_class=JSONResponse,
        status_code=status.HTTP_201_CREATED
    )
    async def create_company(self, company_data: CompanyCreateRequest) -> CompanyResponse:
        company = await company_service.create_company(
            company_data=company_data,
            owner_id=self.current_user.user_id
        )
        return response_with_result_key(company, status_code=status.HTTP_201_CREATED)

    @base_router.get('/{company_id}/', response_model=CompanyResponse)
    async def get_company(self, company_id: int) -> CompanyResponse:
        try:
            company = await company_service.get_company_by_id(company_id=company_id)
            if not company_service.is_visible(company=company, user_id=self.current_user.user_id):
                raise ForbiddenHTTPException()
            return response_with_result_key(company)
        except CompanyNotFoundException:
            raise NotFoundHTTPException()

    @base_router.put('/{company_id}/', response_model=CompanyResponse)
    async def update_company(self, company_id: int, company_data: CompanyUpdateRequest) -> CompanyResponse:
        try:
            company = await company_service.get_company_by_id(company_id=company_id)
        except CompanyNotFoundException:
            raise NotFoundHTTPException()

        if self.current_user.user_id != company.company_owner_id:
            raise ForbiddenHTTPException()

        company = await company_service.update_company(
            company_id=company_id,
            company_data=company_data
        )
        return response_with_result_key(company)

    @base_router.delete(
        '/{company_id}/',
        response_class=JSONResponse,
        status_code=status.HTTP_204_NO_CONTENT)
    async def delete_company(self, company_id: int) -> JSONResponse:
        try:
            company = await company_service.get_company_by_id(company_id=company_id)
        except CompanyNotFoundException:
            raise NotFoundHTTPException()

        if self.current_user.user_id != company.company_owner_id:
            raise ForbiddenHTTPException()

        await company_service.delete_company(company_id=company_id)
        return JSONResponse(content={}, status_code=status.HTTP_204_NO_CONTENT)


@cbv(action_router)
class CompanyActionsCBV:
    current_user: UserResponse = Depends(get_current_user)

    @action_router.get('/{company_id}/members/', response_model=UserListResponse)
    async def get_company_members(self, company_id: int) -> UserListResponse:
        return response_with_result_key(
            await company_service.get_company_members(company_id=company_id)
        )

    @action_router.delete('/{company_id}/members/{member_id}/', response_model=DetailResponse)
    async def kick_company_member(self, company_id: int, member_id: int) -> DetailResponse:
        await company_service.kick_company_member(
            current_user_id=self.current_user.user_id,
            company_id=company_id,
            member_id=member_id
        )

        return DetailResponse(detail=SuccessDetails.SUCCESS)

    @action_router.delete('/{company_id}/leave/', response_model=DetailResponse)
    async def leave_company(self, company_id: int) -> DetailResponse:
        await company_service.leave_company(
            current_user_id=self.current_user.user_id,
            company_id=company_id
        )

        return DetailResponse(detail=SuccessDetails.SUCCESS)

    @action_router.get('/{company_id}/admins/', response_model=AdminListResponse)
    async def get_admins(self, company_id: int) -> AdminListResponse:
        try:
            return response_with_result_key(
                await company_service.get_company_admins(company_id=company_id)
            )
        except CompanyNotFoundException:
            raise NotFoundHTTPException(ExceptionDetails.COMPANY_WITH_ID_NOT_FOUND(company_id))

    @action_router.post('/{company_id}/admins/', response_model=DetailResponse)
    async def add_admin(self, company_id: int, data: AddAdminRequest) -> DetailResponse:
        try:
            await company_service.add_admin(
                user_id=data.user_id,
                company_id=company_id,
                current_user_id=self.current_user.user_id
            )
            return DetailResponse(detail=SuccessDetails.SUCCESS)
        except NotYourCompanyException:
            raise ForbiddenHTTPException(ExceptionDetails.WRONG_COMPANY)
        except CompanyNotFoundException:
            raise NotFoundHTTPException(ExceptionDetails.COMPANY_WITH_ID_NOT_FOUND(company_id))
        except UserNotFoundException:
            raise NotFoundHTTPException(UserExceptionDetails.USER_WITH_ID_NOT_FOUND(data.user_id))

    @action_router.delete('/{company_id}/admins/{admin_id}/', response_model=DetailResponse)
    async def delete_admin(self, company_id: int, admin_id: int) -> DetailResponse:
        try:
            await company_service.kick_company_member(
                current_user_id=self.current_user.user_id,
                company_id=company_id,
                member_id=admin_id
            )
            return DetailResponse(detail=SuccessDetails.SUCCESS)
        except UserNotFoundException:
            raise NotFoundHTTPException(UserExceptionDetails.USER_WITH_ID_NOT_FOUND(admin_id))
        except CompanyNotFoundException:
            raise NotFoundHTTPException(ExceptionDetails.COMPANY_WITH_ID_NOT_FOUND(company_id))
        except NotYourCompanyException:
            raise ForbiddenHTTPException(ExceptionDetails.WRONG_COMPANY)

    @action_router.get('/{company_id}/quizzes/', response_model=Page[QuizFullResponse])
    async def get_quizzes(self, company_id: int, params: Params = Depends()) -> Page[QuizFullResponse]:
        quizzes = await quiz_service.get_company_quizzes(
            company_id=company_id
        )
        pagination = paginate(quizzes, params, items_name='quizzes')
        return response_with_result_key(pagination)
