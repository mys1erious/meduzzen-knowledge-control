from sqlalchemy import DateTime, Column, func, Integer, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.declarative import declared_attr


Base = declarative_base()


class TimeStampModel:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class UserStampModel:
    @declared_attr
    def created_by(self):
        return Column(Integer, ForeignKey("users.id"), nullable=False)

    @declared_attr
    def updated_by(self):
        return Column(Integer, ForeignKey("users.id"), nullable=False)
