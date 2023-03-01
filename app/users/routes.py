from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from fastapi_pagination import Page, Params

from app.core.utils import response_with_result_key
from app.core.exceptions import \
    NotFoundHTTPException, \
    BadRequestHTTPException, \
    UnauthorizedHTTPException, ForbiddenHTTPException
from app.core.pagination import paginate

from .services import user_service
from .schemas import \
    UserResponse, \
    UserSignUpRequest, \
    UserUpdateRequest, \
    TokenResponse
from .exceptions import UserNotFoundException, EmailTakenException, InvalidCredentialsException
from .constants import ExceptionDetails
from .dependencies import get_current_user, UserSignInRequestForm
from .security import create_access_token


router = APIRouter(tags=['Users'], prefix='/users')


@router.post('/sign-in/', response_model=TokenResponse)
async def sign_in_user(form_data: UserSignInRequestForm = Depends()) -> TokenResponse:
    try:
        user = await user_service.authenticate_user(
            email=form_data.user_email,
            password=form_data.user_password
        )
    except (UserNotFoundException, InvalidCredentialsException):
        raise UnauthorizedHTTPException(ExceptionDetails.INVALID_CREDENTIALS)

    access_token = create_access_token(email=user.user_email)
    return response_with_result_key(TokenResponse(
        access_token=access_token,
        token_type='Bearer'
    ))


@router.post('/sign-up/', response_model=UserResponse)
async def sign_up_user(user_data: UserSignUpRequest) -> UserResponse:
    try:
        user = await user_service.register_user(user_data=user_data)
        return response_with_result_key(user)
    except EmailTakenException:
        raise BadRequestHTTPException(ExceptionDetails.EMAIL_TAKEN)


@router.get("/me/", response_model=UserResponse)
async def get_user_me(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    return response_with_result_key(current_user)


@router.get('/', response_model=Page[UserResponse])
async def get_users(
        params: Params = Depends(),
        current_user: UserResponse = Depends(get_current_user)
) -> Page[UserResponse]:
    users = await user_service.get_users()
    pagination = paginate(users.users, params, items_name='users')
    return response_with_result_key(pagination)


@router.get('/{user_id}/', response_model=UserResponse)
async def get_user(
        user_id: int,
        current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    try:
        user = await user_service.get_user_by_id(user_id=user_id)
        return response_with_result_key(user)
    except UserNotFoundException:
        raise NotFoundHTTPException()


@router.put('/{user_id}/', response_model=UserResponse)
async def update_user(
        user_id: int, user_data: UserUpdateRequest,
        current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    if current_user.user_id != user_id:
        raise ForbiddenHTTPException(ExceptionDetails.WRONG_USER)

    try:
        user = await user_service.update_user(
            user_id=user_id,
            user_data=user_data
        )
        return response_with_result_key(user)
    except UserNotFoundException:
        raise NotFoundHTTPException()


@router.delete(
    '/{user_id}/',
    response_class=JSONResponse,
    status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
        user_id: int,
        current_user: UserResponse = Depends(get_current_user)
):
    if current_user.user_id != user_id:
        raise ForbiddenHTTPException(ExceptionDetails.WRONG_USER)

    await user_service.delete_user(user_id=current_user.user_id)
    return JSONResponse(content={}, status_code=status.HTTP_204_NO_CONTENT)
