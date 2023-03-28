from pydantic import EmailStr
from sqlalchemy import select, insert, update, delete, and_

from app.database import database
from app.core.utils import exclude_none
from app.core.exceptions import NotFoundException, ForbiddenException
from app.companies.models import CompanyMembers

from .models import Users
from .schemas import \
    UserListResponse, \
    UserResponse, \
    UserSignUpRequest, \
    UserUpdateRequest
from .security import hash_password, verify_password
from .utils import serialize_user, generate_random_password, get_username_from_email
from .exceptions import \
    UserNotFoundException, \
    EmailTakenException, \
    InvalidCredentialsException
from .constants import ExceptionDetails


class UserService:
    async def get_users(self) -> UserListResponse:
        query = select(Users)
        users = await database.fetch_all(query)
        return UserListResponse(users=[
            serialize_user(user=user)
            for user in users
        ])

    async def get_user_by_id(self, user_id: int) -> UserResponse:
        query = select(Users).where(Users.id == user_id)
        user = await database.fetch_one(query)
        if user is None:
            raise UserNotFoundException(ExceptionDetails.USER_WITH_ID_NOT_FOUND(user_id))
        return serialize_user(user)

    async def get_user_by_email(self, email: str) -> UserResponse:
        user = await self._get_db_user_by_email(email=email)
        if user is None:
            raise UserNotFoundException(ExceptionDetails.USER_WITH_EMAIL_NOT_FOUND(email))
        return serialize_user(user)

    async def register_user(self, user_data: UserSignUpRequest) -> UserResponse:
        user = await self._get_db_user_by_email(email=user_data.user_email)
        if user is not None:
            raise EmailTakenException()

        query = insert(Users).values(
            email=user_data.user_email,
            username=user_data.user_name,
            hashed_password=hash_password(user_data.user_password)
        ).returning(Users)

        user = await database.fetch_one(query)
        return serialize_user(user)

    async def update_user(self, user_id: int, user_data: UserUpdateRequest) -> UserResponse:
        password = user_data.user_password
        hashed_password = hash_password(password) if password else Users.hashed_password

        values = exclude_none({
            'username': user_data.user_name,
            'hashed_password': hashed_password
        })

        query = update(Users) \
            .where(Users.id == user_id) \
            .values(**values) \
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

    async def authenticate_user(self, email: str, password: str) -> UserResponse:
        user = await self._get_db_user_by_email(email=email)
        if not user:
            raise UserNotFoundException(
                ExceptionDetails.USER_WITH_EMAIL_NOT_FOUND(email)
            )
        if not verify_password(
                plain_password=password,
                hashed_password=user.hashed_password):
            raise InvalidCredentialsException(ExceptionDetails.INVALID_CREDENTIALS)
        return serialize_user(user)

    async def register_user_from_3party(self, email: EmailStr) -> UserResponse:
        password = generate_random_password()
        username = get_username_from_email(email)

        user_data = UserSignUpRequest(
            user_email=email,
            user_name=username,
            user_password=password,
            user_password_repeat=password
        )
        return await self.register_user(user_data)

    async def get_user_company_role(self, user_id: int, company_id: int) -> str:
        query = select(CompanyMembers.role).where(and_(
            CompanyMembers.user_id == user_id,
            CompanyMembers.company_id == company_id
        ))
        user = await database.fetch_one(query)
        if user is None:
            raise NotFoundException('Not found')

        return user['role'].value

    async def user_company_is_admin(self, user_id: int, company_id: int):
        # Returns True or raises an exception
        try:
            user_role = await self.get_user_company_role(
                company_id=company_id,
                user_id=user_id
            )
        except NotFoundException:
            raise ForbiddenException(ExceptionDetails.ACTION_NOT_ALLOWED)
        if user_role.lower() not in ['owner', 'admin']:
            raise ForbiddenException(ExceptionDetails.ACTION_NOT_ALLOWED)
        return True

    async def _get_db_user_by_email(self, email: str) -> Users:
        query = select(Users).where(Users.email == email)
        return await database.fetch_one(query)


user_service = UserService()
