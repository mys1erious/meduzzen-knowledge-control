from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy_utils import ChoiceType

from app.core.models import Base, TimeStampModel


class Companies(TimeStampModel, Base):
    __tablename__ = 'companies'

    id = Column('id', Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True, default='')
    visible = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)


class CompanyMembers(Base):
    __tablename__ = 'company_members'

    ROLES = [
        ('member', 'Member'),
        ('owner', 'Owner')
    ]

    id = Column('id', Integer, primary_key=True, index=True)
    role = Column(ChoiceType(ROLES), default='member')
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
