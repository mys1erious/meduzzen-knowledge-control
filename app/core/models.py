from sqlalchemy import DateTime, Column, func
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class TimeStampModel:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
