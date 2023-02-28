import secrets

from pydantic import EmailStr

from .models import Users
from .schemas import UserResponse


def generate_random_password() -> str:
    return secrets.token_urlsafe(16)


def get_username_from_email(email: EmailStr) -> str:
    return email.split('@')[0]


def serialize_user(user: Users) -> UserResponse:
    user_data = UserResponse(
        user_id=user.id,
        user_email=user.email,  # type: ignore
        user_name=user.username,
        user_full_name=user.full_name,
        user_bio=user.bio
    )

    return user_data
