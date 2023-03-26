from sqlalchemy import Integer, Column, String, ForeignKey, Boolean, UniqueConstraint, Float
from sqlalchemy.orm import relationship

from app.core.models import Base, TimeStampModel, UserStampModel


class Quizzes(TimeStampModel, UserStampModel, Base):
    __tablename__ = 'quizzes'

    id = Column('id', Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True, default='')
    # Number that indicates the appearance frequency of the quiz in days
    frequency = Column(Integer, nullable=False)

    __table_args__ = (UniqueConstraint('company_id', 'name', name='company_name_uc'),)


class QuizQuestions(TimeStampModel, Base):
    __tablename__ = 'quiz_questions'

    id = Column('id', Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    content = Column(String, nullable=False)


class QuizAnswers(TimeStampModel, Base):
    __tablename__ = 'quiz_answers'

    id = Column('id', Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("quiz_questions.id"), nullable=False)
    correct = Column(Boolean, default=False, nullable=False)
    content = Column(String, nullable=False)


# TODO: Normalize
class Attempts(TimeStampModel, Base):
    __tablename__ = 'attempts'

    id = Column('id', Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    questions = Column(Integer, nullable=False)
    correct_answers = Column(Float, nullable=False)
    score = Column(Float, nullable=False)
