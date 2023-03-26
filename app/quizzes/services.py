from sqlalchemy import insert, select, asc, update, delete

from app.logging import file_logger
from app.database import database
from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.utils import add_model_label, exclude_none
from app.core.constants import ExceptionDetails
from app.users.services import user_service
from app.users.schemas import UserResponse
from app.users.constants import ExceptionDetails as UserExceptionDetails

from .models import Quizzes, QuizQuestions, QuizAnswers
from .schemas import QuizResponse, QuizCreateRequest, QuestionResponse, AnswerResponse, QuizFullResponse, \
    QuestionFullResponse, QuizUpdateRequest, QuestionCreateRequest, QuestionUpdateRequest, AnswerCreateRequest, \
    AnswerUpdateRequest
from ..core.schemas import DetailResponse


class QuizService:
    async def get_quizzes(self) -> list[QuizFullResponse]:
        query = self.select_full_quiz_query()
        quiz_records = await database.fetch_all(query)
        return self.serialize_quiz_full_records(quiz_records)

    async def create_quiz(self, current_user_id: int, data: QuizCreateRequest) -> DetailResponse:
        await user_service.user_company_is_admin(
            user_id=current_user_id,
            company_id=data.company_id
        )

        try:
            async with database.transaction():
                quiz = await database.fetch_one(self.insert_quiz_query(
                    user_id=current_user_id,
                    data=data
                ))

                question_values = [
                    {
                        'content': question.content,
                        'quiz_id': quiz.id
                    }
                    for question in data.questions
                ]
                create_questions_query = insert(QuizQuestions).values(question_values).returning(QuizQuestions)
                questions = await database.fetch_all(create_questions_query)

                answer_values = [
                    {
                        'content': answer.content,
                        'correct': answer.correct,
                        'question_id': questions[i].id
                    }
                    for i, question in enumerate(data.questions)
                    for answer in question.answers
                ]
                create_answers_query = insert(QuizAnswers).values(answer_values)
                await database.fetch_all(create_answers_query)
        except Exception as e:
            return DetailResponse(detail=f'{e}')
        return DetailResponse(detail='success')

    async def get_quiz(self, quiz_id: int) -> QuizFullResponse:
        query = self.select_full_quiz_query().filter(
            Quizzes.id == quiz_id
        )
        quiz_records = await database.fetch_all(query)
        if not quiz_records:
            raise NotFoundException()
        return self.serialize_quiz_full_records(quiz_records)[0]

    async def update_quiz(self, quiz_id: int, current_user_id: int, data: QuizUpdateRequest) -> QuizResponse:
        quiz_company_id = await self.get_company_id_by_quiz_id(quiz_id)
        await user_service.user_company_is_admin(
            user_id=current_user_id,
            company_id=quiz_company_id
        )

        values = exclude_none({
            'name': data.name,
            'description': data.description,
            'frequency': data.frequency
        })

        query = update(Quizzes) \
            .where(Quizzes.id == quiz_id) \
            .values(**values) \
            .returning(Quizzes)
        quiz = await database.fetch_one(query)
        if quiz is None:
            raise NotFoundException(ExceptionDetails.ENTITY_WITH_ID_NOT_FOUND('quiz', quiz_id))

        quiz = self.serialize_quiz(quiz)
        return quiz

    async def delete_quiz(self, quiz_id: int, current_user_id: int) -> DetailResponse:
        quiz_company_id = await self.get_company_id_by_quiz_id(quiz_id)
        await user_service.user_company_is_admin(
            user_id=current_user_id,
            company_id=quiz_company_id
        )

        try:
            async with database.transaction():
                questions_query = select(QuizQuestions.id).where(QuizQuestions.quiz_id == quiz_id)
                question_id_records = await database.fetch_all(questions_query)
                question_ids = [record['id'] for record in question_id_records]
                file_logger.info(question_ids)

                delete_answers_query = delete(QuizAnswers).where(QuizAnswers.question_id.in_(question_ids))
                delete_questions_query = delete(QuizQuestions).where(QuizQuestions.quiz_id == quiz_id)
                delete_quiz_query = delete(Quizzes).where(Quizzes.id == quiz_id)

                await database.fetch_all(delete_answers_query)
                await database.fetch_all(delete_questions_query)
                await database.fetch_one(delete_quiz_query)
        except Exception as e:
            return DetailResponse(detail=f'{e}')
        return DetailResponse(detail='success')

    async def get_company_quizzes(self, company_id: int) -> list[QuizFullResponse]:
        query = self.select_full_quiz_query().filter(
            Quizzes.company_id == company_id
        )
        quiz_records = await database.fetch_all(query)
        return self.serialize_quiz_full_records(quiz_records)

    async def get_quiz_by_id(self, quiz_id: int) -> QuizResponse:
        query = select(Quizzes).where(Quizzes.id == quiz_id)
        quiz = await database.fetch_one(query)

        if quiz is None:
            raise NotFoundException(ExceptionDetails.ENTITY_WITH_ID_NOT_FOUND('quiz', quiz_id))
        return self.serialize_quiz(quiz)

    async def get_company_id_by_quiz_id(self, quiz_id: int):
        record = await database.fetch_one(
            select(Quizzes.company_id).filter(
                Quizzes.id == quiz_id
            )
        )
        if not record:
            raise NotFoundException()
        return record['company_id']

    def select_full_quiz_query(self):
        return select(
            add_model_label(Quizzes) +
            add_model_label(QuizQuestions) +
            add_model_label(QuizAnswers)
        ).join(
            QuizQuestions, Quizzes.id == QuizQuestions.quiz_id
        ).join(
            QuizAnswers, QuizQuestions.id == QuizAnswers.question_id
        ).order_by(
            asc(Quizzes.id),
            asc(QuizQuestions.id),
            asc(QuizAnswers.id)
        )

    def insert_quiz_query(self, user_id: int, data: QuizCreateRequest):
        return insert(Quizzes).values(
            company_id=data.company_id,
            name=data.name,
            description=data.description,
            frequency=data.frequency,
            created_by=user_id,
            updated_by=user_id
        ).returning(Quizzes)

    def serialize_quiz_full_records(self, records) -> list[QuizFullResponse]:
        # NOTE: Only to be used with self.select_full_quiz_query()
        #   as it assumes that query is ordered by quiz_id, question_id, answer_id
        quiz_responses = {}

        prev_question_id = None
        prev_answer_id = None
        cur_question = None
        for record in records:
            quiz = quiz_responses.get(record.quizzes_id, None)

            if quiz is None:
                quiz = quiz_responses[record.quizzes_id] = QuizFullResponse(
                    quiz_id=record.quizzes_id,
                    company_id=record.quizzes_company_id,
                    name=record.quizzes_name,
                    description=record.quizzes_description,
                    frequency=record.quizzes_frequency,
                    created_by=record.quizzes_created_by,
                    updated_by=record.quizzes_updated_by,
                    questions=[]
                )

            if prev_question_id != record.quiz_questions_id:
                cur_question = QuestionFullResponse(
                    question_id=record.quiz_questions_id,
                    quiz_id=record.quizzes_id,
                    content=record.quiz_questions_content,
                    answers=[]
                )
                quiz.questions.append(cur_question)

            if prev_answer_id != record.quiz_answers_id:
                answer = AnswerResponse(
                    answer_id=record.quiz_answers_id,
                    question_id=record.quiz_questions_id,
                    content=record.quiz_answers_content,
                    correct=record.quiz_answers_correct
                )
                cur_question.answers.append(answer)

            if prev_question_id != record.quiz_questions_id:
                prev_question_id = record.quiz_questions_id
            if prev_answer_id != record.quiz_answers_id:
                prev_answer_id = record.quiz_answers_id

        return list(quiz_responses.values())

    def serialize_quiz(self, quiz: Quizzes) -> QuizResponse:
        return QuizResponse(
            name=quiz.name,
            description=quiz.description,
            frequency=quiz.frequency,
            quiz_id=quiz.id,
            company_id=quiz.company_id,
            created_by=quiz.created_by,
            updated_by=quiz.updated_by
        )

    # ---- Questions ----
    async def get_questions(self) -> list[QuestionFullResponse]:
        query = self.select_full_question_query()
        question_records = await database.fetch_all(query)
        return self.serialize_question_full_records(question_records)

    async def get_quiz_questions(self, quiz_id: int) -> list[QuestionFullResponse]:
        query = self.select_full_question_query().filter(QuizQuestions.quiz_id == quiz_id)
        question_records = await database.fetch_all(query)
        return self.serialize_question_full_records(question_records)

    async def add_question(
            self,
            current_user_id: int,
            data: QuestionCreateRequest
    ) -> DetailResponse:
        quiz_company_id = await self.get_company_id_by_quiz_id(data.quiz_id)
        await user_service.user_company_is_admin(
            user_id=current_user_id,
            company_id=quiz_company_id
        )

        try:
            async with database.transaction():
                create_questions_query = insert(QuizQuestions).values(
                    content=data.content,
                    quiz_id=data.quiz_id
                ).returning(QuizQuestions)
                question = await database.fetch_one(create_questions_query)

                answer_values = [
                    {
                        'content': answer.content,
                        'correct': answer.correct,
                        'question_id': question.id
                    } for answer in data.answers
                ]
                create_answers_query = insert(QuizAnswers).values(answer_values)
                await database.fetch_all(create_answers_query)
        except Exception as e:
            return DetailResponse(detail=f'{e}')
        return DetailResponse(detail='success')

    async def get_question(self, question_id: int) -> QuestionFullResponse:
        query = self.select_full_question_query().filter(
            QuizQuestions.id == question_id
        )
        question_records = await database.fetch_all(query)
        if not question_records:
            raise NotFoundException()
        return self.serialize_question_full_records(question_records)[0]

    async def update_question(
            self,
            question_id: int,
            current_user_id: int,
            data: QuestionUpdateRequest
    ) -> QuestionResponse:
        company_id = await self.get_company_id_by_question_id(question_id)
        await user_service.user_company_is_admin(
            user_id=current_user_id,
            company_id=company_id
        )

        values = exclude_none({'content': data.content})
        query = update(QuizQuestions) \
            .where(QuizQuestions.id == question_id) \
            .values(**values) \
            .returning(QuizQuestions)
        question = await database.fetch_one(query)
        if question is None:
            raise NotFoundException(ExceptionDetails.ENTITY_WITH_ID_NOT_FOUND('question', question_id))

        return self.serialize_question(question)

    async def delete_question(self, question_id: int, current_user_id: int) -> DetailResponse:
        company_id = await self.get_company_id_by_question_id(question_id)
        await user_service.user_company_is_admin(
            user_id=current_user_id,
            company_id=company_id
        )

        try:
            async with database.transaction():
                questions_query = select(QuizQuestions.id).where(QuizQuestions.id == question_id)
                question = await database.fetch_one(questions_query)

                delete_answers_query = delete(QuizAnswers).where(QuizAnswers.question_id == question.id)
                delete_question_query = delete(QuizQuestions).where(QuizQuestions.id == question_id)

                await database.fetch_all(delete_answers_query)
                await database.fetch_one(delete_question_query)
        except Exception as e:
            return DetailResponse(detail=f'{e}')
        return DetailResponse(detail='success')

    async def get_company_id_by_question_id(self, question_id: int):
        query = select(Quizzes.company_id).join(
            QuizQuestions, QuizQuestions.quiz_id == Quizzes.id
        )
        record = await database.fetch_one(query)
        if not record:
            raise NotFoundException()
        return record['company_id']

    def select_full_question_query(self):
        return select(
            add_model_label(QuizQuestions) +
            add_model_label(QuizAnswers)
        ).join(
            QuizAnswers, QuizQuestions.id == QuizAnswers.question_id
        ).order_by(
            asc(QuizQuestions.id),
            asc(QuizAnswers.id)
        )

    def serialize_question_full_records(self, records) -> list[QuestionFullResponse]:
        # NOTE: Only to be used with self.select_full_question_query()
        #   as it assumes that query is ordered by question_id, answer_id
        question_responses = {}

        prev_answer_id = None
        for record in records:
            question = question_responses.get(record.quiz_questions_id, None)

            if question is None:
                question = question_responses[record.quiz_questions_id] = QuestionFullResponse(
                    question_id=record.quiz_questions_id,
                    quiz_id=record.quiz_questions_quiz_id,
                    content=record.quiz_questions_content,
                    answers=[]
                )

            if prev_answer_id != record.quiz_answers_id:
                answer = AnswerResponse(
                    answer_id=record.quiz_answers_id,
                    question_id=record.quiz_questions_id,
                    content=record.quiz_answers_content,
                    correct=record.quiz_answers_correct
                )
                question.answers.append(answer)

            if prev_answer_id != record.quiz_answers_id:
                prev_answer_id = record.quiz_answers_id

        return list(question_responses.values())

    def serialize_question(self, question: QuizQuestions) -> QuestionResponse:
        return QuestionResponse(
            quiz_id=question.quiz_id,
            content=question.content,
            question_id=question.id
        )

    # ---- Answers ----
    async def get_answers(self) -> list[AnswerResponse]:
        query = select(QuizAnswers)
        answers = await database.fetch_all(query)
        return [self.serialize_answer(answer) for answer in answers]

    async def get_question_answers(self, question_id: int) -> list[AnswerResponse]:
        query = select(QuizAnswers).filter(QuizAnswers.question_id == question_id)
        answers = await database.fetch_all(query)
        return [self.serialize_answer(answer) for answer in answers]

    async def add_answer(
            self,
            current_user_id: int,
            data: AnswerCreateRequest
    ) -> DetailResponse:
        quiz_company_id = await self.get_company_id_by_question_id(data.question_id)
        await user_service.user_company_is_admin(
            user_id=current_user_id,
            company_id=quiz_company_id
        )

        try:
            async with database.transaction():
                answer_values = {
                    'content': data.content,
                    'correct': data.correct,
                    'question_id': data.question_id
                }
                create_answers_query = insert(QuizAnswers).values(answer_values)
                await database.fetch_one(create_answers_query)
        except Exception as e:
            return DetailResponse(detail=f'{e}')
        return DetailResponse(detail='success')

    async def get_answer(self, answer_id: int) -> AnswerResponse:
        query = select(QuizAnswers).filter(
            QuizAnswers.id == answer_id
        )
        answer = await database.fetch_one(query)
        if not answer:
            raise NotFoundException()
        return self.serialize_answer(answer)

    async def update_answer(
            self,
            answer_id: int,
            current_user_id: int,
            data: AnswerUpdateRequest
    ) -> AnswerResponse:
        company_id = await self.get_company_id_by_answer_id(answer_id)
        await user_service.user_company_is_admin(
            user_id=current_user_id,
            company_id=company_id
        )

        values = exclude_none({
            'content': data.content,
            'correct': data.correct
        })
        query = update(QuizAnswers) \
            .where(QuizAnswers.id == answer_id) \
            .values(**values) \
            .returning(QuizAnswers)
        answer = await database.fetch_one(query)
        if answer is None:
            raise NotFoundException(ExceptionDetails.ENTITY_WITH_ID_NOT_FOUND('answer', answer_id))

        return self.serialize_answer(answer)

    async def delete_answer(self, answer_id: int, current_user_id: int) -> DetailResponse:
        company_id = await self.get_company_id_by_answer_id(answer_id)
        await user_service.user_company_is_admin(
            user_id=current_user_id,
            company_id=company_id
        )

        try:
            query = delete(QuizAnswers).where(QuizAnswers.id == answer_id)
            await database.fetch_one(query)
        except Exception as e:
            return DetailResponse(detail=f'{e}')
        return DetailResponse(detail='success')

    async def get_company_id_by_answer_id(self, answer_id: int):
        query = select(Quizzes.company_id).join(
            QuizQuestions, QuizQuestions.quiz_id == Quizzes.id
        ).join(
            QuizAnswers, QuizAnswers.id == answer_id
        )
        record = await database.fetch_one(query)
        if not record:
            raise NotFoundException()
        return record['company_id']

    def serialize_answer(self, answer: QuizAnswers) -> AnswerResponse:
        return AnswerResponse(
            question_id=answer.question_id,
            correct=answer.correct,
            content=answer.content,
            answer_id=answer.id
        )


quiz_service = QuizService()
