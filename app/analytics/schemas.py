from datetime import datetime

from pydantic import BaseModel, root_validator

from app.core.schemas import root_validator_round_floats


class ScoreAvgResponse(BaseModel):
    quiz_id: int = None
    user_id: int = None
    company_id: int = None
    total_questions: int
    total_correct_answers: float
    avg_score: float

    @root_validator(pre=True)
    def round_values(cls, values):
        return root_validator_round_floats(values)


class ScoreTimeResponse(BaseModel):
    avg_score: float
    created_at: datetime

    @root_validator(pre=True)
    def round_values(cls, values):
        return root_validator_round_floats(values)


class QuizScoresTimeResponse(BaseModel):
    quiz_id: int
    result: list[ScoreTimeResponse]


class UserScoresTimeResponse(BaseModel):
    user_id: int
    result: list[ScoreTimeResponse]


class QuizTimeResponse(BaseModel):
    quiz_id: int
    created_at: datetime


class UserTimeResponse(BaseModel):
    user_id: int
    created_at: datetime
