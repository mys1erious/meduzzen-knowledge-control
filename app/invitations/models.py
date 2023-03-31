from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy_utils import ChoiceType

from app.core.models import TimeStampModel, Base


class Invitations(TimeStampModel, Base):
    __tablename__ = 'invitations'

    TYPES = [
        ('invitation', 'Invitation'),
        ('join_request', 'Join Request')
    ]

    id = Column('id', Integer, primary_key=True, index=True)
    message = Column(String, nullable=True, default='')
    type = Column(ChoiceType(TYPES))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
