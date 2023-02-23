import databases

from app.config import settings


database = databases.Database(settings.POSTGRES_URL)
