from fastapi import APIRouter, Depends, status
from fastapi .responses import JSONResponse
from fastapi_pagination import Page, Params

from app.core.utils import response_with_result_key
from app.core.exceptions import NotFoundHTTPException, BadRequestHTTPException
from app.core.pagination import paginate

from .services import user_service
from .schemas import UserResponse, UserSignUpRequest, UserUpdateRequest
from .exceptions import UserNotFoundException, EmailTakenException
from .constants import ExceptionDetails


router = APIRouter(tags=['Users'], prefix='/users')


@router.get('/', response_model=Page[UserResponse])
async def get_users(params: Params = Depends()) -> Page[UserResponse]:
    users = await user_service.get_users()
    pagination = paginate(users.users, params, items_name='users')
    return response_with_result_key(pagination)


@router.post('/', response_model=UserResponse)
async def sign_up_user(user_data: UserSignUpRequest) -> UserResponse:
    try:
        user = await user_service.register_user(user_data=user_data)
        return response_with_result_key(user)
    except EmailTakenException:
        raise BadRequestHTTPException(ExceptionDetails.EMAIL_TAKEN)


@router.get('/{user_id}/', response_model=UserResponse)
async def get_user(user_id: int) -> UserResponse:
    try:
        user = await user_service.get_user_by_id(user_id=user_id)
        return response_with_result_key(user)
    except UserNotFoundException:
        raise NotFoundHTTPException()


@router.put('/{user_id}/', response_model=UserResponse)
async def update_user(user_id: int, user_data: UserUpdateRequest) -> UserResponse:
    try:
        user = await user_service.update_user(
            user_id=user_id,
            user_data=user_data
        )
        return response_with_result_key(user)
    except UserNotFoundException:
        raise NotFoundHTTPException()


@router.delete('/{user_id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int) -> None:
    try:
        await user_service.delete_user(user_id=user_id)
    except UserNotFoundException:
        raise NotFoundHTTPException()
