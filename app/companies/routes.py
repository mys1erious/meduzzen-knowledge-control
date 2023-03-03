from fastapi import APIRouter, status, Depends
from fastapi.responses import JSONResponse
from fastapi_pagination import Page, Params

from app.core.exceptions import ForbiddenHTTPException, NotFoundHTTPException
from app.core.utils import response_with_result_key
from app.core.pagination import paginate
from app.users.dependencies import get_current_user
from app.users.schemas import UserResponse

from .schemas import CompanyCreateRequest, CompanyResponse, CompanyListResponse, CompanyUpdateRequest
from .services import company_service
from .exceptions import CompanyNotFoundException


router = APIRouter(
    tags=['Companies'],
    prefix='/companies',
)


@router.get('/', response_model=Page[CompanyResponse])
async def get_companies(
    params: Params = Depends(),
    current_user: UserResponse = Depends(get_current_user)
) -> CompanyListResponse:
    companies = await company_service.get_companies(user_id=current_user.user_id)
    pagination = paginate(companies.companies, params, items_name='companies')
    return response_with_result_key(pagination)


@router.post(
    '/',
    response_model=CompanyResponse,
    response_class=JSONResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_company(
        company_data: CompanyCreateRequest,
        current_user: UserResponse = Depends(get_current_user)
) -> CompanyResponse:
    company = await company_service.create_company(
        company_data=company_data,
        owner_id=current_user.user_id
    )

    return response_with_result_key(company, status_code=status.HTTP_201_CREATED)


@router.get('/{company_id}/', response_model=CompanyResponse)
async def get_company(
        company_id: int,
        current_user: UserResponse = Depends(get_current_user)
) -> CompanyResponse:
    try:
        company = await company_service.get_company_by_id(company_id=company_id)

        if not company_service.is_visible(company=company, user_id=current_user.user_id):
            raise ForbiddenHTTPException()

        return response_with_result_key(company)
    except CompanyNotFoundException:
        raise NotFoundHTTPException()


@router.put('/{company_id}/', response_model=CompanyResponse)
async def update_company(
        company_id: int, company_data: CompanyUpdateRequest,
        current_user: UserResponse = Depends(get_current_user)
) -> CompanyResponse:
    try:
        company = await company_service.get_company_by_id(company_id=company_id)
    except CompanyNotFoundException:
        raise NotFoundHTTPException()

    if current_user.user_id != company.company_owner_id:
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
async def delete_company(
        company_id: int,
        current_user: UserResponse = Depends(get_current_user)
) -> JSONResponse:
    try:
        company = await company_service.get_company_by_id(company_id=company_id)
    except CompanyNotFoundException:
        raise NotFoundHTTPException()

    if current_user.user_id != company.company_owner_id:
        raise ForbiddenHTTPException()

    await company_service.delete_company(company_id=company_id)
    return JSONResponse(content={}, status_code=status.HTTP_204_NO_CONTENT)
