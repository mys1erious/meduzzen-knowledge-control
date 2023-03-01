from pydantic import BaseSettings, PostgresDsn, RedisDsn
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

    # Databases
    POSTGRES_URL: PostgresDsn
    REDIS_URL: RedisDsn
    POSTGRES_URL_TEST: PostgresDsn

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
