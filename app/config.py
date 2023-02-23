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

    # Databases
    POSTGRES_URL: PostgresDsn
    REDIS_URL: RedisDsn


settings = Settings()
