# Hope its enough :D Anyway most of the logic is tested in other test files
#   added some mocking in here as you asked on the meetings
from unittest.mock import AsyncMock, patch, MagicMock
import pytest

from app.core.exceptions import NotFoundException, BadRequestException
from app.logging import file_logger
from app.quizzes.models import QuizAnswers
from app.quizzes.services import quiz_service
from app.users.services import user_service


@pytest.fixture
def db():
    mock_db = AsyncMock()
    yield mock_db


# ---- Users ----
async def test_get_user_company_role_found(db):
    mock_row = MagicMock()
    mock_row.role = {'role': 'admin'}
    db.fetch_one.return_value = mock_row

    with patch('app.users.services.database', db):
        user_role = await user_service.get_user_company_role(user_id=1, company_id=1)

    db.fetch_one.assert_called_once()
    assert user_role == mock_row.role


async def test_get_user_company_role_not_found(db):
    db.fetch_one.return_value = None

    with patch('app.users.services.database', db), pytest.raises(NotFoundException):
        await user_service.get_user_company_role(user_id=1, company_id=1)


# ---- Quizzes ----
async def test_get_attempt_score():
    total_correct_answers = {'v1': 10, 'v2': 5, 'v3': 8}
    correct_answers = 12.5
    result = round(await quiz_service.get_attempt_score(total_correct_answers, correct_answers), 1)
    assert result == 0.5


async def test_get_total_answers_per_question(db):
    expected_question_ids = [1, 2, 3]
    data = [
        {'question_id': 1, 'num': 5},
        {'question_id': 2, 'num': 10},
        {'question_id': 3, 'num': 15},
    ]
    db.fetch_all.return_value = data

    with patch('app.quizzes.services.database', db):
        result = await quiz_service.get_total_answers_per_question(expected_question_ids)

    assert result == {1: 5, 2: 10, 3: 15}


async def test_get_total_submitted_answers_per_question(db):
    answers = [
        QuizAnswers(question_id=1),
        QuizAnswers(question_id=1),
        QuizAnswers(question_id=1),
        QuizAnswers(question_id=2),
        QuizAnswers(question_id=2),
        QuizAnswers(question_id=3)
    ]
    expected_result = {1: 3, 2: 2, 3: 1}

    with patch('app.quizzes.services.database', db):
        result = await quiz_service.get_total_submitted_answers_per_question(answers)
    assert result == expected_result


@pytest.fixture
def questions():
    return [
        MagicMock(id=1),
        MagicMock(id=2),
        MagicMock(id=3),
    ]

@pytest.fixture
def answer_ids():
    return [
        [1],
        [2, 3],
        [4, 5],
    ]

@pytest.fixture
def answers():
    return [
        MagicMock(id=1, question_id=1),
        MagicMock(id=2, question_id=2),
        MagicMock(id=3, question_id=2),
        MagicMock(id=4, question_id=3),
        MagicMock(id=5, question_id=3),
    ]


async def test_get_validated_attempt_answers(questions, answer_ids, answers, db):
    db.fetch_all.return_value = answers
    with patch('app.quizzes.services.database', db):
        validated_answers = await quiz_service.get_validated_attempt_answers(questions, answer_ids)
    assert validated_answers == answers


async def test_get_validated_attempt_answers_missing_answer(questions, answer_ids, answers, db):
    del answers[2] # remove one answer
    db.fetch_all.return_value = answers
    with pytest.raises(BadRequestException, match="Some of submitted answers dont belong to its question"), \
            patch('app.quizzes.services.database', db):
        await quiz_service.get_validated_attempt_answers(questions, answer_ids)


async def test_get_validated_attempt_answers_duplicate_answer(questions, answer_ids, answers, db):
    answer_ids[1].append(3) # add duplicate answer
    db.fetch_all.return_value = answers
    with pytest.raises(BadRequestException, match="you have duplicated answers"), \
            patch('app.quizzes.services.database', db):
        await quiz_service.get_validated_attempt_answers(questions, answer_ids)


async def test_get_validated_attempt_answers_missing_answer_per_question(questions, answer_ids, answers, db):
    answer_ids[1] = [] # empty answer list for one question
    db.fetch_all.return_value = answers
    with pytest.raises(BadRequestException, match="You need to give at least one answer per question"), \
            patch('app.quizzes.services.database', db):
        await quiz_service.get_validated_attempt_answers(questions, answer_ids)


async def test_get_validated_attempt_questions_returns_questions(questions, db):
    question_ids = [question.id for question in questions]
    db.fetch_all.return_value = questions
    with patch('app.quizzes.services.database', db):
        validated_questions = await quiz_service.get_validated_attempt_questions(quiz_id=1, question_ids=question_ids)
    assert len(validated_questions) == len(questions)
    for question in questions:
        assert question in validated_questions


async def test_get_validated_attempt_questions_raises_error_on_incorrect_question_ids(questions, db):
    question_ids = [question.id for question in questions]
    db.fetch_all.return_value = questions
    # add a fake question id that doesn't belong to any quiz
    question_ids.append(999)
    with patch('app.quizzes.services.database', db), pytest.raises(BadRequestException):
        await quiz_service.get_validated_attempt_questions(quiz_id=1, question_ids=question_ids)


async def test_get_validated_attempt_questions_raises_error_on_missing_question_answers(questions, db):
    question_ids = [question.id for question in questions]
    db.fetch_all.return_value = questions
    # remove one question id from the list
    question_ids.pop()
    with patch('app.quizzes.services.database', db), pytest.raises(BadRequestException):
        await quiz_service.get_validated_attempt_questions(quiz_id=1, question_ids=question_ids)
