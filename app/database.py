import databases
from sqlalchemy import MetaData

from app.config import settings


metadata = MetaData()

database = databases.Database(settings.POSTGRES_URL)


def get_db():
    return database
