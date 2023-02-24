import databases
from sqlalchemy import create_engine, MetaData

from app.config import settings


engine = create_engine(settings.POSTGRES_URL)
metadata = MetaData()

database = databases.Database(settings.POSTGRES_URL)


def get_db():
    return database
