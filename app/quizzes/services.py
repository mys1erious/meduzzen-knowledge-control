import datetime

from databases.backends.postgres import Record
from sqlalchemy import insert, select, asc, update, delete, and_, func

from app.logging import file_logger
from app.database import database, get_redis
from app.core.exceptions import NotFoundException, BadRequestException
from app.core.utils import add_model_label, exclude_none
from app.core.constants import ExceptionDetails, SuccessDetails
from app.core.schemas import DetailResponse
from app.users.services import user_service

from app.quizzes.models import Quizzes, QuizQuestions, QuizAnswers, Attempts
from app.quizzes.schemas import QuizResponse, QuizCreateRequest, QuestionResponse, AnswerResponse, QuizFullResponse, \
    QuestionFullResponse, QuizUpdateRequest, QuestionCreateRequest, QuestionUpdateRequest, AnswerCreateRequest, \
    AnswerUpdateRequest, SubmitAttemptRequest, AttemptResponse, QuizStatsResponse, AttemptRedisSchema


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
        return DetailResponse(detail=SuccessDetails.SUCCESS)

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

                delete_answers_query = delete(QuizAnswers).where(QuizAnswers.question_id.in_(question_ids))
                delete_questions_query = delete(QuizQuestions).where(QuizQuestions.quiz_id == quiz_id)
                delete_quiz_query = delete(Quizzes).where(Quizzes.id == quiz_id)

                await database.fetch_all(delete_answers_query)
                await database.fetch_all(delete_questions_query)
                await database.fetch_one(delete_quiz_query)
        except Exception as e:
            return DetailResponse(detail=f'{e}')
        return DetailResponse(detail=SuccessDetails.SUCCESS)

    async def get_quiz_questions(self, quiz_id: int) -> list[QuestionFullResponse]:
        query = self.select_full_question_query().filter(QuizQuestions.quiz_id == quiz_id)
        question_records = await database.fetch_all(query)
        return self.serialize_question_full_records(question_records)

    async def submit_attempt(self, current_user_id: int, data: SubmitAttemptRequest) -> AttemptResponse:
        company_id = await self.get_company_id_by_quiz_id(data.quiz_id)
        await user_service.user_company_is_member(
            user_id=current_user_id,
            company_id=company_id
        )

        questions = await self.get_validated_attempt_questions(data.quiz_id, data.question_ids)
        answers = await self.get_validated_attempt_answers(questions, data.answer_ids)

        total_correct_answers = await self.get_total_correct_answers_per_question(data.question_ids)
        correct_answers = await self.calculate_correct_answers(
            total_correct_answers=total_correct_answers,
            question_ids=data.question_ids,
            answers=answers
        )
        score = await self.get_attempt_score(
            total_correct_answers=total_correct_answers,
            correct_answers=correct_answers
        )

        values = {
            'quiz_id': data.quiz_id,
            'user_id': current_user_id,
            'questions': len(questions),
            'correct_answers': correct_answers,
            'score': score
        }

        insert_query = insert(Attempts).values(values).returning(Attempts)
        attempt = await database.fetch_one(insert_query)

        for answer in answers:
            await self.store_attempt_in_redis(
                quiz_id=data.quiz_id,
                user_id=current_user_id,
                company_id=company_id,
                question_id=answer.question_id,
                answer_id=answer.id,
                correct=1 if answer.correct else 0
            )

        return self.serialize_attempt(attempt)

    async def store_attempt_in_redis(
            self,
            quiz_id: int,
            user_id: int,
            company_id: int,
            question_id: int,
            answer_id: int,
            correct: int
    ) -> None:
        redis = await get_redis()

        key = f'quiz_id:{quiz_id}-user_id:{user_id}-company_id:{company_id}'
        data = AttemptRedisSchema(
            quiz_id=quiz_id,
            user_id=user_id,
            company_id=company_id,
            question_id=question_id,
            answer_id=answer_id,
            correct=correct
        ).dict()

        exp = datetime.timedelta(hours=48)
        exp_seconds = int(exp.total_seconds())

        await redis.hset(key, mapping=data)
        await redis.expire(key, exp_seconds)

    async def get_attempt_score(self, total_correct_answers, correct_answers: float):
        total_correct_answers = sum(total_correct_answers.values())
        score = correct_answers / total_correct_answers
        return score

    async def calculate_correct_answers(
            self,
            total_correct_answers,
            question_ids:
            list[int],
            answers: list[QuizAnswers]
    ) -> float:
        correct_submitted_answers = await self.get_correct_submitted_answers_per_question(answers)
        total_submitted_answers = await self.get_total_submitted_answers_per_question(answers)

        total_score = 0
        for question_id in question_ids:
            correct_total = total_correct_answers[question_id]
            total_submitted = total_submitted_answers[question_id]
            correct_submitted = correct_submitted_answers[question_id]

            submitted_dif = correct_submitted / total_submitted
            correct_dif = correct_submitted / correct_total
            score = submitted_dif * correct_dif
            total_score += score

        return total_score

    async def get_total_answers_per_question(self, question_ids: list[int]):
        query = select(
            QuizAnswers.question_id,
            func.count().label('num')
        ).filter(
            QuizAnswers.question_id.in_(question_ids),
        ).group_by(QuizAnswers.question_id)
        res = await database.fetch_all(query)
        return {row['question_id']: row['num'] for row in res}

    async def get_total_correct_answers_per_question(self, question_ids: list[int]):
        query = select(
            QuizAnswers.question_id,
            func.count().label('num')
        ).filter(
            QuizAnswers.question_id.in_(question_ids),
            QuizAnswers.correct == True
        ).group_by(QuizAnswers.question_id)
        res = await database.fetch_all(query)
        return {row['question_id']: row['num'] for row in res}

    async def get_total_submitted_answers_per_question(self, answers: list[QuizAnswers]):
        map = {}
        for answer in answers:
            if answer.question_id not in map:
                map[answer.question_id] = 1
            else:
                map[answer.question_id] += 1
        return map

    async def get_correct_submitted_answers_per_question(self, answers: list[QuizAnswers]):
        map = {}
        for answer in answers:
            if answer.question_id not in map:
                map[answer.question_id] = 0
            if answer.correct:
                map[answer.question_id] += 1
        return map

    async def get_validated_attempt_answers(
            self,
            questions: list[QuizQuestions],
            answer_ids: list[list[int]]
    ) -> list[QuizAnswers]:
        for question_answer_ids in answer_ids:
            if not len(question_answer_ids) > 0:
                raise BadRequestException('You need to give at least one answer per question')

        flat_answer_ids = [
            answer_id
            for question_answer_ids in answer_ids
            for answer_id in question_answer_ids
        ]

        quiz_question_ids = [question.id for question in questions]
        answers_query = select(QuizAnswers).filter(and_(
            QuizAnswers.question_id.in_(quiz_question_ids),
            QuizAnswers.id.in_(flat_answer_ids)
        ))
        answers: list[QuizAnswers] = await database.fetch_all(answers_query)

        if len(answers) != len(flat_answer_ids):
            raise BadRequestException(
                'Some of submitted answers dont belong to its question or you have duplicated answers'
            )

        question_answer_mapping = {question.id: set() for question in questions}
        for question, question_answer_ids in zip(questions, answer_ids):
            for answer_id in question_answer_ids:
                question_answer_mapping[question.id].add(answer_id)

        for answer in answers:
            if answer.id not in question_answer_mapping[answer.question_id]:
                raise BadRequestException(
                    'Some of submitted answers dont belong to its question'
                )

        return answers

    async def get_validated_attempt_questions(self, quiz_id: int, question_ids: list[int]) -> list[QuizQuestions]:
        questions_query = select(
            QuizQuestions,
        ).filter(and_(
            QuizQuestions.quiz_id == quiz_id,
            QuizQuestions.id.in_(question_ids)
        ))
        questions = await database.fetch_all(questions_query)

        if len(questions) != len(question_ids):
            raise BadRequestException(
                'You didnt submit answers to all quiz questions or some questions dont belong to this quiz'
            )

        return questions

    def serialize_attempt(self, attempt: Attempts) -> AttemptResponse:
        return AttemptResponse(
            attempt_id=attempt.id,
            quiz_id=attempt.quiz_id,
            user_id=attempt.user_id,
            taken_at=attempt.created_at,
            questions=attempt.questions,
            correct_answers=attempt.correct_answers,
            score=attempt.score
        )

    async def get_quiz_stats(
            self,
            current_user_id: int,
            quiz_id: int | None,
            user_id: int | None,
            company_id: int | None
    ) -> QuizStatsResponse:
        query = select(
            func.sum(Attempts.questions).label('total_questions'),
            func.sum(Attempts.correct_answers).label('total_correct_answers'),
            func.avg(Attempts.score).label('avg_score')
        )

        if quiz_id:
            company_id = await self.get_company_id_by_quiz_id(quiz_id)
            await user_service.user_company_is_member(current_user_id, company_id)

            query = query.filter(Attempts.quiz_id == quiz_id)
        if user_id:
            query = query.filter(Attempts.user_id == user_id)
        if company_id:
            await user_service.user_company_is_member(current_user_id, company_id)

            query = query.join(
                Quizzes, Quizzes.id == Attempts.quiz_id
            ).filter(
                Quizzes.company_id == company_id
            )

        ids = exclude_none({
            'quiz_id': quiz_id,
            'user_id': user_id,
            'company_id': company_id
        })
        stats = await database.fetch_one(query)

        if not stats['avg_score']:
            raise NotFoundException()

        return self.serialize_quiz_stats(
            stats=stats,
            ids=ids
        )

    def serialize_quiz_stats(self, stats: Record, ids: dict) -> QuizStatsResponse:
        return QuizStatsResponse(
            **ids,
            total_questions=stats.total_questions,
            total_correct_answers=stats.total_correct_answers,
            avg_score=stats.avg_score
        )

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
            raise NotFoundException(ExceptionDetails.ENTITY_WITH_ID_NOT_FOUND('quiz', quiz_id))
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
        return DetailResponse(detail=SuccessDetails.SUCCESS)

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
        return DetailResponse(detail=SuccessDetails.SUCCESS)

    async def get_question_answers(self, question_id: int) -> list[AnswerResponse]:
        query = select(QuizAnswers).filter(QuizAnswers.question_id == question_id)
        answers = await database.fetch_all(query)
        return [self.serialize_answer(answer) for answer in answers]

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
        return DetailResponse(detail=SuccessDetails.SUCCESS)

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
        return DetailResponse(detail=SuccessDetails.SUCCESS)

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
