from pydantic import BaseSettings, PostgresDsn, RedisDsn, EmailStr
from app.constants import Environment


class Settings(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    # App
    APP_VERSION: str = "0.0.1"
    ENVIRONMENT: Environment = Environment.PRODUCTION
    HOST: str
    PORT: int
    CORS_ORIGINS: list[str]
    CORS_HEADERS: list[str]
    ADMIN_EMAIL: EmailStr

    # Databases
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_DB: str
    POSTGRES_URL: PostgresDsn = None
    POSTGRES_URL_TEST: PostgresDsn = None
    REDIS_URL: RedisDsn
    REDIS_URL_TEST: RedisDsn = None

    # Auth
    JWT_ALGORITHM: str
    JWT_SECRET_KEY: str
    JWT_ACCESS_TOKEN_EXPIRE_IN_SECONDS: int

    AUTH0_ALGORITHMS: str
    AUTH0_AUDIENCE: str
    AUTH0_DOMAIN: str
    AUTH0_ISSUER: str
    AUTH0_RULE_NAMESPACE: str


settings = Settings()
# settings.POSTGRES_URL = f'postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}' \
settings.POSTGRES_URL = f'postgresql://ubuntu' \
                        f'@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}'
