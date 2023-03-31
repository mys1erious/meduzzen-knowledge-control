from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from fastapi_pagination import Page, Params
from fastapi_utils.cbv import cbv

from app.core.utils import response_with_result_key
from app.core.exceptions import \
    NotFoundHTTPException, \
    BadRequestHTTPException, \
    UnauthorizedHTTPException, ForbiddenHTTPException
from app.core.pagination import paginate

from app.users.services import user_service
from app.users.schemas import \
    UserResponse, \
    UserSignUpRequest, \
    UserUpdateRequest, \
    TokenResponse
from app.users.exceptions import UserNotFoundException, EmailTakenException, InvalidCredentialsException
from app.users.constants import ExceptionDetails
from app.users.dependencies import get_current_user, UserSignInRequestForm
from app.users.security import create_access_token


auth_router = APIRouter(tags=['Auth'])
users_router = APIRouter(tags=['Users'])


@cbv(auth_router)
class AuthCBV:
    @auth_router.post('/sign-in/', response_model=TokenResponse)
    async def sign_in_user(self, form_data: UserSignInRequestForm = Depends()) -> TokenResponse:
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

    @auth_router.post('/sign-up/', response_model=UserResponse)
    async def sign_up_user(self, user_data: UserSignUpRequest) -> UserResponse:
        try:
            user = await user_service.register_user(user_data=user_data)
            return response_with_result_key(user)
        except EmailTakenException:
            raise BadRequestHTTPException(ExceptionDetails.EMAIL_TAKEN)


@cbv(users_router)
class UsersCBV:
    current_user: UserResponse = Depends(get_current_user)

    @users_router.get('/', response_model=Page[UserResponse])
    async def get_users(self, params: Params = Depends()) -> Page[UserResponse]:
        users = await user_service.get_users()
        pagination = paginate(users.users, params, items_name='users')
        return response_with_result_key(pagination)

    @users_router.get("/me/", response_model=UserResponse)
    async def get_user_me(self) -> UserResponse:
        return response_with_result_key(self.current_user)

    @users_router.get('/{user_id}/', response_model=UserResponse)
    async def get_user(self, user_id: int) -> UserResponse:
        try:
            user = await user_service.get_user_by_id(user_id=user_id)
            return response_with_result_key(user)
        except UserNotFoundException:
            raise NotFoundHTTPException()

    @users_router.put('/{user_id}/', response_model=UserResponse)
    async def update_user(self, user_id: int, user_data: UserUpdateRequest) -> UserResponse:
        if self.current_user.user_id != user_id:
            raise ForbiddenHTTPException(ExceptionDetails.WRONG_USER)

        try:
            user = await user_service.update_user(
                user_id=user_id,
                user_data=user_data
            )
            return response_with_result_key(user)
        except UserNotFoundException:
            raise NotFoundHTTPException()

    @users_router.delete(
        '/{user_id}/',
        response_class=JSONResponse,
        status_code=status.HTTP_204_NO_CONTENT)
    async def delete_user(self, user_id: int):
        if self.current_user.user_id != user_id:
            raise ForbiddenHTTPException(ExceptionDetails.WRONG_USER)

        await user_service.delete_user(user_id=self.current_user.user_id)
        return JSONResponse(content={}, status_code=status.HTTP_204_NO_CONTENT)
