from sqlalchemy import Column, Integer, String
from app.core.models import Base, TimeStampModel


class Users(TimeStampModel, Base):
    __tablename__ = 'users'

    id = Column('id', Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False)
    full_name = Column(String, default='', nullable=True)
    bio = Column(String, default='', nullable=True)
    hashed_password = Column(String, nullable=False)
