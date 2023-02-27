from sqlalchemy import select, insert, update, delete

from app.database import database
from app.core.utils import exclude_none

from .models import Users
from .schemas import UserListResponse, UserResponse, UserSignUpRequest, UserUpdateRequest
from .security import hash_password
from .utils import serialize_user
from .exceptions import UserNotFoundException, EmailTakenException
from .constants import ExceptionDetails


class UserService:
    async def get_users(self) -> UserListResponse:
        query = select(Users)
        users = await database.fetch_all(query)
        return UserListResponse(users=[
            serialize_user(user)
            for user in users
        ])

    async def get_user_by_id(self, user_id: int) -> UserResponse:
        query = select(Users).where(Users.id == user_id)
        user = await database.fetch_one(query)
        if user is None:
            raise UserNotFoundException(ExceptionDetails.USER_WITH_ID_NOT_FOUND(user_id))
        return serialize_user(user)

    async def register_user(self, user_data: UserSignUpRequest) -> UserResponse:
        query = select(Users).where(Users.email == user_data.user_email)
        user_exists = await database.fetch_one(query) is not None
        if user_exists:
            raise EmailTakenException()

        query = insert(Users).values(
            email=user_data.user_email,
            username=user_data.user_name,
            hashed_password=hash_password(user_data.user_password)
        ).returning(Users)

        user = await database.fetch_one(query)
        user = serialize_user(user)
        return user

    async def update_user(self, user_id: int, user_data: UserUpdateRequest) -> UserResponse:
        password = user_data.user_password
        hashed_password = hash_password(password) if password else Users.hashed_password

        values = exclude_none({
            'email': user_data.user_email,
            'username': user_data.user_name,
            'full_name': user_data.user_full_name,
            'bio': user_data.user_bio,
            'hashed_password': hashed_password
        })

        query = update(Users)\
            .where(Users.id == user_id)\
            .values(**values)\
            .returning(Users)

        user = await database.fetch_one(query)
        if user is None:
            raise UserNotFoundException(ExceptionDetails.USER_WITH_ID_NOT_FOUND(user_id))

        user = serialize_user(user)
        return user

    async def delete_user(self, user_id: int) -> None:
        query = delete(Users).where(Users.id == user_id).returning(Users)
        user = await database.fetch_one(query)
        if user is None:
            raise UserNotFoundException(ExceptionDetails.USER_WITH_ID_NOT_FOUND(user_id))


user_service = UserService()
