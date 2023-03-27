from fastapi import APIRouter, Depends, status
from fastapi.responses import Response
from fastapi_pagination import Page, Params
from fastapi_utils.cbv import cbv

from app.core.pagination import paginate
from app.core.utils import response_with_result_key
from app.core.exceptions import ForbiddenException, ForbiddenHTTPException, NotFoundException, NotFoundHTTPException, \
    BadRequestException, BadRequestHTTPException
from app.core.schemas import DetailResponse
from app.core.constants import SuccessDetails
from app.users.dependencies import get_current_user
from app.users.schemas import UserResponse
from app.users.constants import ExceptionDetails as UserExceptionDetails

from .schemas import QuizFullResponse, QuizCreateRequest, QuizResponse, QuizUpdateRequest, QuestionFullResponse, \
    QuestionCreateRequest, QuestionResponse, QuestionUpdateRequest, AnswerResponse, AnswerCreateRequest, \
    AnswerUpdateRequest, SubmitAttemptRequest, AttemptResponse
from .services import quiz_service


quiz_router = APIRouter(tags=['Quizzes'])
question_router = APIRouter(tags=['Questions'])
answer_router = APIRouter(tags=['Answers'])
attempt_router = APIRouter(tags=['Attempts'])


@cbv(attempt_router)
class AttemptsCBV:
    current_user: UserResponse = Depends(get_current_user)

    @attempt_router.post('/', response_model=AttemptResponse)
    async def submit_attempt(self, data: SubmitAttemptRequest) -> AttemptResponse:
        try:
            return await quiz_service.submit_attempt(
                current_user_id=self.current_user.user_id,
                data=data
            )
        except NotFoundException as e:
            raise NotFoundHTTPException(str(e))
        except ForbiddenException as e:
            raise ForbiddenHTTPException(str(e))
        except BadRequestException as e:
            raise BadRequestHTTPException(str(e))


@cbv(quiz_router)
class QuizzesCBV:
    current_user: UserResponse = Depends(get_current_user)

    @quiz_router.get('/', response_model=Page[QuizFullResponse])
    async def get_all_quizzes(self, params: Params = Depends()) -> Page[QuizFullResponse]:
        quizzes = await quiz_service.get_quizzes()
        pagination = paginate(quizzes, params, items_name='quizzes')
        return response_with_result_key(pagination)

    @quiz_router.post('/', status_code=201, response_model=DetailResponse)
    async def create_quiz(self, response: Response, data: QuizCreateRequest) -> DetailResponse:
        try:
            res = await quiz_service.create_quiz(
                current_user_id=self.current_user.user_id,
                data=data
            )
            if res.detail != SuccessDetails.SUCCESS:
                response.status_code = status.HTTP_400_BAD_REQUEST
            return res
        except ForbiddenException:
            raise ForbiddenHTTPException(UserExceptionDetails.ACTION_NOT_ALLOWED)

    @quiz_router.get('/{quiz_id}/', response_model=QuizFullResponse)
    async def get_quiz(self, quiz_id: int) -> QuizFullResponse:
        try:
            quiz = await quiz_service.get_quiz(quiz_id)
            return response_with_result_key(quiz)
        except NotFoundException:
            raise NotFoundHTTPException()

    @quiz_router.put('/{quiz_id}/', response_model=QuizResponse)
    async def update_quiz(self, quiz_id: int, data: QuizUpdateRequest) -> QuizResponse:
        try:
            quiz = await quiz_service.update_quiz(
                current_user_id=self.current_user.user_id,
                quiz_id=quiz_id,
                data=data
            )
            return response_with_result_key(quiz)
        except NotFoundException:
            raise NotFoundHTTPException()
        except ForbiddenException:
            raise ForbiddenHTTPException(UserExceptionDetails.ACTION_NOT_ALLOWED)

    @quiz_router.delete('/{quiz_id}/', response_model=DetailResponse)
    async def delete_quiz(self, response: Response, quiz_id: int) -> DetailResponse | Response:
        try:
            res = await quiz_service.delete_quiz(
                current_user_id=self.current_user.user_id,
                quiz_id=quiz_id
            )
            if res.detail != SuccessDetails.SUCCESS:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return res

            return Response(status_code=204)
        except NotFoundException:
            raise NotFoundHTTPException()
        except ForbiddenException:
            raise ForbiddenHTTPException(UserExceptionDetails.ACTION_NOT_ALLOWED)

    @quiz_router.get('/{quiz_id}/questions/', response_model=list[QuestionFullResponse])
    async def get_quiz_questions(self, quiz_id: int) -> list[QuestionFullResponse]:
        questions = await quiz_service.get_quiz_questions(quiz_id)
        return response_with_result_key(questions)


@cbv(question_router)
class QuestionsCBV:
    current_user: UserResponse = Depends(get_current_user)

    @question_router.get('/', response_model=list[QuestionFullResponse])
    async def get_all_questions(self) -> list[QuestionFullResponse]:
        questions = await quiz_service.get_questions()
        return response_with_result_key(questions)

    @question_router.post('/', status_code=201, response_model=DetailResponse)
    async def add_question(self, response: Response, data: QuestionCreateRequest) -> DetailResponse:
        try:
            res = await quiz_service.add_question(
                current_user_id=self.current_user.user_id,
                data=data
            )
            if res.detail != SuccessDetails.SUCCESS:
                response.status_code = status.HTTP_400_BAD_REQUEST
            return res
        except NotFoundException:
            raise NotFoundHTTPException()
        except ForbiddenException:
            raise ForbiddenHTTPException(UserExceptionDetails.ACTION_NOT_ALLOWED)

    @question_router.get('/{question_id}/', response_model=QuestionFullResponse)
    async def get_question(self, question_id: int) -> QuestionFullResponse:
        try:
            question = await quiz_service.get_question(question_id)
            return response_with_result_key(question)
        except NotFoundException:
            raise NotFoundHTTPException()

    @question_router.put('/{question_id}/', response_model=QuestionResponse)
    async def update_question(self, question_id: int, data: QuestionUpdateRequest) -> QuestionResponse:
        try:
            question = await quiz_service.update_question(
                current_user_id=self.current_user.user_id,
                question_id=question_id,
                data=data
            )
            return response_with_result_key(question)
        except NotFoundException:
            raise NotFoundHTTPException()
        except ForbiddenException:
            raise ForbiddenHTTPException(UserExceptionDetails.ACTION_NOT_ALLOWED)

    @question_router.delete('/{question_id}/', response_model=DetailResponse)
    async def delete_question(self, response: Response, question_id: int) -> DetailResponse | Response:
        try:
            res = await quiz_service.delete_question(
                current_user_id=self.current_user.user_id,
                question_id=question_id
            )
            if res.detail != SuccessDetails.SUCCESS:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return res

            return Response(status_code=204)
        except NotFoundException:
            raise NotFoundHTTPException()
        except ForbiddenException:
            raise ForbiddenHTTPException(UserExceptionDetails.ACTION_NOT_ALLOWED)

    @question_router.get('/{question_id}/answers/', response_model=list[AnswerResponse])
    async def get_question_answers(self, question_id: int) -> list[AnswerResponse]:
        answers = await quiz_service.get_question_answers(question_id)
        return response_with_result_key(answers)


@cbv(answer_router)
class AnswersCBV:
    current_user: UserResponse = Depends(get_current_user)

    @answer_router.get('/', response_model=list[AnswerResponse])
    async def get_all_answers(self) -> list[AnswerResponse]:
        answers = await quiz_service.get_answers()
        return response_with_result_key(answers)

    @answer_router.post('/', status_code=201, response_model=DetailResponse)
    async def add_answer(self, response: Response, data: AnswerCreateRequest) -> DetailResponse:
        try:
            res = await quiz_service.add_answer(
                current_user_id=self.current_user.user_id,
                data=data
            )
            if res.detail != SuccessDetails.SUCCESS:
                response.status_code = status.HTTP_400_BAD_REQUEST
            return res
        except NotFoundException:
            raise NotFoundHTTPException()
        except ForbiddenException:
            raise ForbiddenHTTPException(UserExceptionDetails.ACTION_NOT_ALLOWED)

    @answer_router.get('/{answer_id}/', response_model=AnswerResponse)
    async def get_answer(self, answer_id: int) -> AnswerResponse:
        try:
            answer = await quiz_service.get_answer(answer_id)
            return response_with_result_key(answer)
        except NotFoundException:
            raise NotFoundHTTPException()

    @answer_router.put('/{answer_id}/', response_model=AnswerResponse)
    async def update_answer(self, answer_id: int, data: AnswerUpdateRequest) -> AnswerResponse:
        try:
            answer = await quiz_service.update_answer(
                current_user_id=self.current_user.user_id,
                answer_id=answer_id,
                data=data
            )
            return response_with_result_key(answer)
        except NotFoundException:
            raise NotFoundHTTPException()
        except ForbiddenException:
            raise ForbiddenHTTPException(UserExceptionDetails.ACTION_NOT_ALLOWED)

    @answer_router.delete('/{answer_id}/', response_model=DetailResponse)
    async def delete_answer(self, response: Response, answer_id: int) -> DetailResponse | Response:
        try:
            res = await quiz_service.delete_answer(
                current_user_id=self.current_user.user_id,
                answer_id=answer_id
            )
            if res.detail != SuccessDetails.SUCCESS:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return res

            return Response(status_code=204)
        except NotFoundException:
            raise NotFoundHTTPException()
        except ForbiddenException:
            raise ForbiddenHTTPException(UserExceptionDetails.ACTION_NOT_ALLOWED)
