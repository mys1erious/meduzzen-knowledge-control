from fastapi import APIRouter, status, Depends
from fastapi.responses import JSONResponse
from fastapi_pagination import Page, Params
from fastapi_utils.cbv import cbv

from app.core.exceptions import ForbiddenHTTPException, NotFoundHTTPException
from app.core.utils import response_with_result_key
from app.core.pagination import paginate
from app.core.schemas import DetailResponse
from app.users.dependencies import get_current_user
from app.users.schemas import UserResponse, UserListResponse

from .schemas import CompanyCreateRequest, CompanyResponse, CompanyListResponse, CompanyUpdateRequest
from .services import company_service
from .exceptions import CompanyNotFoundException


router = APIRouter(tags=['Companies'])


@cbv(router)
class CompaniesCBV:
    current_user: UserResponse = Depends(get_current_user)

    @router.get('/', response_model=Page[CompanyResponse])
    async def get_companies(self, params: Params = Depends()) -> CompanyListResponse:
        companies = await company_service.get_companies(user_id=self.current_user.user_id)
        pagination = paginate(companies.companies, params, items_name='companies')
        return response_with_result_key(pagination)

    @router.post(
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

    @router.get('/{company_id}/', response_model=CompanyResponse)
    async def get_company(self, company_id: int) -> CompanyResponse:
        try:
            company = await company_service.get_company_by_id(company_id=company_id)
            if not company_service.is_visible(company=company, user_id=self.current_user.user_id):
                raise ForbiddenHTTPException()
            return response_with_result_key(company)
        except CompanyNotFoundException:
            raise NotFoundHTTPException()

    @router.put('/{company_id}/', response_model=CompanyResponse)
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

    @router.delete(
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

    @router.get('/{company_id}/members/', response_model=UserListResponse)
    async def get_company_members(self, company_id: int) -> UserListResponse:
        return response_with_result_key(
            await company_service.get_company_members(company_id=company_id)
        )

    @router.delete('/{company_id}/members/{member_id}/', response_model=DetailResponse)
    async def kick_company_member(self, company_id: int, member_id: int) -> DetailResponse:
        await company_service.kick_company_member(
            current_user_id=self.current_user.user_id,
            company_id=company_id,
            member_id=member_id
        )

        return DetailResponse(detail='success')

    @router.delete('/{company_id}/leave/', response_model=DetailResponse)
    async def leave_company(self, company_id: int) -> DetailResponse:
        await company_service.leave_company(
            current_user_id=self.current_user.user_id,
            company_id=company_id
        )

        return DetailResponse(detail='success')
