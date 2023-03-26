from pydantic import BaseModel, validator, constr


# ---- Answers ----
class AnswerBaseSchema(BaseModel):
    correct: bool = None
    content: str = None


class AnswerResponse(AnswerBaseSchema):
    question_id: int
    answer_id: int


class AnswerCreateRequest(AnswerBaseSchema):
    question_id: int = None
    pass


class AnswerUpdateRequest(AnswerBaseSchema):
    pass


# ---- Questions ----
class QuestionBaseSchema(BaseModel):
    content: str = None


class QuestionResponse(QuestionBaseSchema):
    quiz_id: int
    question_id: int


class QuestionFullResponse(QuestionResponse):
    answers: list[AnswerResponse]


class QuestionCreateRequest(QuestionBaseSchema):
    quiz_id: int = None
    answers: list[AnswerCreateRequest]

    @validator('answers')
    def validate_answers(cls, v: list):
        if len(v) < 2:
            raise ValueError('answers list must have at least 2 items')
        return v


class QuestionUpdateRequest(QuestionBaseSchema):
    pass


# ---- Quizzes ----
class QuizBaseSchema(BaseModel):
    name: constr(min_length=1)
    description: str = None
    frequency: int = None


class QuizResponse(QuizBaseSchema):
    quiz_id: int
    company_id: int
    created_by: int
    updated_by: int


class QuizFullResponse(QuizResponse):
    questions: list[QuestionFullResponse]


class QuizCreateRequest(QuizBaseSchema):
    company_id: int
    questions: list[QuestionCreateRequest]

    @validator('questions')
    def validate_questions(cls, v: list):
        if len(v) < 2:
            raise ValueError('questions list must have at least 2 items')
        return v


class QuizUpdateRequest(QuizBaseSchema):
    pass
