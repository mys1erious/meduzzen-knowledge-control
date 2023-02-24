from datetime import datetime
from pydantic import BaseModel, EmailStr


# For List response list[UserBaseSchema]
class UserBaseSchema(BaseModel):
    user_email: EmailStr | None = None
    user_name: str | None = None
    user_full_name: str | None = None


class UserSignInSchema(BaseModel):
    user_email: EmailStr | None = None
    user_password: str


class UserSignUpSchema(UserBaseSchema):
    user_email: EmailStr
    user_name: str
    user_password: str
    user_password_repeat: str


class UserUpdateSchema(UserBaseSchema):
    password: str | None = None


class UserDBSchema(UserBaseSchema):
    id: int
    hashed_password: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
