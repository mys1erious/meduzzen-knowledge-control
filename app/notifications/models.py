from sqlalchemy import String, Column, Boolean, Integer, ForeignKey

from app.core.models import TimeStampModel, Base, UserStampModel


class Notifications(TimeStampModel, UserStampModel, Base):
    __tablename__ = 'notifications'

    id = Column('id', Integer, primary_key=True, index=True)
    status = Column(String, nullable=False)
    text = Column(String, nullable=True, default='')
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
