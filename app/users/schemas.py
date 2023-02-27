from typing import Callable

from pydantic import BaseModel, EmailStr, validator
from .constants import ExceptionDetails


def valid_password(password) -> str:
    if len(password) < 5:
        raise ValueError(ExceptionDetails.WEAK_PASSWORD)
    return password


def password_repeat_match(password_repeat: str, values: dict) -> str:
    password = values.get('user_password')
    if password and password_repeat != password:
        raise ValueError(ExceptionDetails.PASSWORDS_DONT_MATCH)
    return password_repeat


class UserBaseSchema(BaseModel):
    user_email: EmailStr
    user_name: str


class UserResponse(UserBaseSchema):
    user_id: int
    user_full_name: str | None = None
    user_bio: str | None = None


class UserListResponse(BaseModel):
    users: list[UserResponse]


class UserSignUpRequest(UserBaseSchema):
    user_password: str
    user_password_repeat: str

    # validators
    _ensure_user_password_is_valid: classmethod = validator(
        "user_password",
        allow_reuse=True
    )(valid_password)
    _ensure_user_password_is_match: classmethod = validator(
        "user_password_repeat",
        allow_reuse=True
    )(password_repeat_match)


class UserUpdateRequest(BaseModel):
    user_email: EmailStr | None = None
    user_name: str | None = None
    user_full_name: str | None = None
    user_bio: str | None = None
    user_password: str | None = None
    user_password_repeat: str | None = None

    # validators
    _ensure_user_password_is_valid: classmethod = validator(
        "user_password",
        allow_reuse=True
    )(valid_password)
    _ensure_user_password_is_match: classmethod = validator(
        "user_password_repeat",
        allow_reuse=True
    )(password_repeat_match)
