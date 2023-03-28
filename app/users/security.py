import json
from datetime import timedelta, datetime
from urllib.request import urlopen

from fastapi.security import HTTPBearer
from passlib.context import CryptContext
from jose import jwt, JWTError
from pydantic import EmailStr

from app.config import settings

from app.users.constants import ExceptionDetails
from app.users.exceptions import InvalidCredentialsException, InvalidTokenException
from app.users.schemas import TokenDataSchema, JwksSchema, JwksKeySchema

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

token_scheme = HTTPBearer(
    bearerFormat='Bearer',
    scheme_name='Token Auth',
    description='Auth with JWT or Auth0 Tokens'
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(email: EmailStr, expires_delta: timedelta | None = None) -> str:
    to_encode = {"sub": email}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            seconds=settings.JWT_ACCESS_TOKEN_EXPIRE_IN_SECONDS
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> TokenDataSchema:
    try:
        return decode_jwt_token(token)
    except (JWTError, InvalidTokenException):
        pass

    try:
        return decode_auth0_token(token)
    except (JWTError, InvalidTokenException):
        raise InvalidTokenException(ExceptionDetails.INVALID_TOKEN)


def decode_jwt_token(token: str) -> TokenDataSchema:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        email = payload.get("sub")
        if email is None:
            raise InvalidCredentialsException(ExceptionDetails.INVALID_CREDENTIALS)
        return TokenDataSchema(user_email=email)

    except JWTError:
        raise InvalidTokenException(ExceptionDetails.INVALID_TOKEN)


def get_rsa_key(token: str) -> JwksKeySchema:
    r = urlopen(f'https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json')
    keys = json.loads(r.read())['keys']
    jwks = JwksSchema(keys=[JwksKeySchema(**key) for key in keys])

    unverified_header = jwt.get_unverified_header(token)
    for key in jwks.keys:
        if key.kid == unverified_header.get('kid', ''):
            return key

    msg = 'Invalid kid header (wrong tenant or rotated public key)'
    raise InvalidTokenException(msg)


def decode_auth0_token(token: str) -> TokenDataSchema:
    try:
        rsa_key = get_rsa_key(token)

        payload = jwt.decode(
            token,
            rsa_key.dict(),
            algorithms=settings.AUTH0_ALGORITHMS,
            audience=settings.AUTH0_AUDIENCE,
            issuer=f'https://{settings.AUTH0_DOMAIN}/'
        )

        email = payload.get(f'{settings.AUTH0_RULE_NAMESPACE}/email')
        if email is None:
            raise InvalidCredentialsException(ExceptionDetails.INVALID_CREDENTIALS)
        return TokenDataSchema(user_email=email, type='auth0')

    except JWTError:
        raise InvalidTokenException(ExceptionDetails.INVALID_TOKEN)
