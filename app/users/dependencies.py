from fastapi import Depends, Form
from pydantic import EmailStr

from app.config import settings
from app.core.exceptions import UnauthorizedHTTPException
from app.core.constants import ExceptionDetails as CoreExceptionDetails
from app.users.constants import ExceptionDetails
from app.users.exceptions import InvalidTokenException, UserNotFoundException
from app.users.schemas import UserResponse
from app.users.security import token_scheme, decode_token
from app.users.services import user_service


async def get_current_user(token: str = Depends(token_scheme)) -> UserResponse:
    try:
        token_data = decode_token(token.credentials)  # type: ignore
    except InvalidTokenException:
        raise UnauthorizedHTTPException(ExceptionDetails.INVALID_TOKEN)

    try:
        return await user_service.get_user_by_email(email=token_data.user_email)
    except UserNotFoundException:
        if token_data.type == 'auth0':
            return await user_service.register_user_from_3party(
                email=token_data.user_email
            )

        raise UnauthorizedHTTPException(ExceptionDetails.INVALID_CREDENTIALS)


async def get_admin_user(current_user: UserResponse = Depends(get_current_user)):
    if current_user.user_email != settings.ADMIN_EMAIL:
        raise UnauthorizedHTTPException(CoreExceptionDetails.NOT_ALLOWED)
    return current_user


# I Don't think it's possible to make a pydantic model with
#   fields as Form() and then use those fields in the endpoint
#   as it asks for the form_data instead of fields themselves.
#
# So this form is created as normal class based on
#   'OAuth2PasswordRequestForm' in fastapi source code.
#   https://github.com/tiangolo/fastapi/blob/master/fastapi/security/oauth2.py
class UserSignInRequestForm:
    def __init__(
            self,
            user_email: EmailStr = Form(),
            user_password: str = Form(),
    ):
        self.user_email = user_email
        self.user_password = user_password
