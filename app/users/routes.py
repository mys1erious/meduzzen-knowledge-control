from fastapi import APIRouter

from app.core.utils import response_with_result_key
from app.core.exceptions import NotFoundHTTPException, BadRequestHTTPException

from .services import user_service
from .schemas import UserResponse, UserSignUpRequest, UserUpdateRequest, UserListResponse
from .exceptions import UserNotFoundException, EmailTakenException
from .constants import ExceptionDetails

router = APIRouter(tags=['Users'], prefix='/users')


@router.get('/', response_model=UserListResponse)
async def get_users():
    users = await user_service.get_users()
    return response_with_result_key(users)


@router.post('/', response_model=UserResponse)
async def sign_up_user(user_data: UserSignUpRequest):
    try:
        user = await user_service.register_user(user_data)
        return response_with_result_key(user)
    except EmailTakenException:
        raise BadRequestHTTPException(ExceptionDetails.EMAIL_TAKEN)


@router.get('/{user_id}/', response_model=UserResponse)
async def get_user(user_id: int):
    try:
        user = await user_service.get_user_by_id(user_id)
        return response_with_result_key(user)
    except UserNotFoundException:
        raise NotFoundHTTPException()


@router.put('/{user_id}/', response_model=UserResponse)
async def update_user(user_id: int, user_data: UserUpdateRequest):
    try:
        user = await user_service.update_user(user_id, user_data)
        return response_with_result_key(user)
    except UserNotFoundException:
        raise NotFoundHTTPException()


@router.delete('/{user_id}/')
async def delete_user(user_id: int):
    try:
        await user_service.delete_user(user_id)
    except UserNotFoundException:
        raise NotFoundHTTPException()
