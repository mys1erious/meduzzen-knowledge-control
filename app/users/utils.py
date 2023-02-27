from .models import Users
from .schemas import UserResponse


def serialize_user(user: Users) -> UserResponse:
    user_data = UserResponse(
        user_id=user.id,
        user_email=user.email,  # type: ignore
        user_name=user.username,
        user_full_name=user.full_name,
        user_bio=user.bio
    )

    return user_data
