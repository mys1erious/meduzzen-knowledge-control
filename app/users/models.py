from sqlalchemy import Table, Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import metadata


users_model = Table(
    'users',
    metadata,
    Column('id', Integer, primary_key=True, index=True),
    Column('email', String, unique=True, nullable=False, index=True),
    Column('username', String, unique=True, nullable=False),
    Column('full_name', String, default=''),
    Column('hashed_password', String, nullable=False),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
    Column('updated_at', DateTime(timezone=True), onupdate=func.now()),
)
