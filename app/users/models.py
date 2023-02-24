from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.core.models import Base


class Users(Base):
    __tablename__ = 'user'

    id = Column('id', Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False)
    full_name = Column(String, default='', nullable=True)
    bio = Column(String, default='', nullable=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
