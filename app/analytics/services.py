from datetime import datetime, timedelta

from databases.backends.postgres import Record
from sqlalchemy import select, func, desc

from app.analytics.schemas import ScoreAvgResponse, ScoreTimeResponse, QuizScoresTimeResponse, QuizTimeResponse, \
    UserTimeResponse, UserScoresTimeResponse
from app.companies.models import CompanyMembers
from app.core.exceptions import NotFoundException
from app.core.utils import exclude_none
from app.database import database
from app.quizzes.models import Attempts, Quizzes
from app.quizzes.services import quiz_service
from app.users.services import user_service


class AnalyticsService:
    async def get_avg_score(
            self,
            current_user_id: int,
            quiz_id: int | None,
            user_id: int | None,
            company_id: int | None
    ) -> ScoreAvgResponse:
        query = select(
            func.sum(Attempts.questions).label('total_questions'),
            func.sum(Attempts.correct_answers).label('total_correct_answers'),
            func.avg(Attempts.score).label('avg_score')
        )

        if quiz_id:
            company_id = await quiz_service.get_company_id_by_quiz_id(quiz_id)
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
            raise NotFoundException('Not Found')

        return self.serialize_score_avg(
            stats=stats,
            ids=ids
        )

    async def get_user_last_attempts(self, user_id: int) -> list[QuizTimeResponse]:
        query = select(
            Attempts.quiz_id,
            func.max(Attempts.created_at).label('max_created_at')
        ).filter(
            Attempts.user_id == user_id
        ).group_by(Attempts.quiz_id)
        records = await database.fetch_all(query)

        return [
            QuizTimeResponse(
                quiz_id=record.quiz_id,
                created_at=record.max_created_at,
            )
            for record in records
        ]

    async def get_user_avg_scores_by_time(
            self,
            current_user_id: int,
            user_id: int,
            company_id: int = None
    ) -> list[QuizScoresTimeResponse]:
        if company_id:
            await user_service.user_company_is_admin(
                user_id=current_user_id,
                company_id=company_id
            )
        if user_id != current_user_id:
            await user_service.user_company_is_member(
                user_id=user_id,
                company_id=company_id
            )

        query = select(
            Attempts.quiz_id,
            Attempts.created_at,
            Attempts.score
        ).filter(
            Attempts.user_id == user_id
        ).order_by(Attempts.quiz_id, Attempts.created_at)
        attempts = await database.fetch_all(query)

        response_data = []

        # Couldn't manage to replace this loop logic with query but still there are no nested loops,
        #   so it should be fine performance-wise
        prev_quiz_id = None
        cur_quiz = None
        cur_avg = 0
        for attempt in attempts:
            if not prev_quiz_id or attempt.quiz_id != prev_quiz_id:
                cur_quiz = QuizScoresTimeResponse(
                    quiz_id=attempt.quiz_id,
                    result=[]
                )
                response_data.append(cur_quiz)
                cur_avg = 0

            n = len(cur_quiz.result) + 1
            cur_avg = (cur_avg * (n - 1) + attempt.score) / n
            cur_quiz.result.append(ScoreTimeResponse(
                avg_score=cur_avg,
                created_at=attempt.created_at
            ))

            if not prev_quiz_id or attempt.quiz_id != prev_quiz_id:
                prev_quiz_id = attempt.quiz_id

        return response_data

    async def get_members_avg_scores_by_time(
            self,
            current_user_id: int,
            company_id: int
    ) -> list[UserScoresTimeResponse]:
        if company_id:
            await user_service.user_company_is_admin(
                user_id=current_user_id,
                company_id=company_id
            )

        query = select(
            Attempts.user_id,
            Attempts.quiz_id,
            Attempts.created_at,
            Attempts.score
        ).join(
            Quizzes, Quizzes.id == Attempts.quiz_id
        ).filter(
            Quizzes.company_id == company_id
        ).order_by(Attempts.user_id, Attempts.created_at)
        attempts = await database.fetch_all(query)

        response_data = []

        prev_user_id = None
        cur_item = None
        cur_avg = 0
        for attempt in attempts:
            if not prev_user_id or attempt.user_id != prev_user_id:
                cur_item = UserScoresTimeResponse(
                    user_id=attempt.user_id,
                    result=[]
                )
                response_data.append(cur_item)
                cur_avg = 0

            n = len(cur_item.result) + 1
            cur_avg = (cur_avg * (n - 1) + attempt.score) / n
            cur_item.result.append(ScoreTimeResponse(
                avg_score=cur_avg,
                created_at=attempt.created_at
            ))

            if not prev_user_id or attempt.user_id != prev_user_id:
                prev_user_id = attempt.user_id

        return response_data

    async def get_members_last_attempt(self, company_id: int, current_user_id: int):
        await user_service.user_company_is_admin(
            user_id=current_user_id,
            company_id=company_id
        )

        members_query = select(
            CompanyMembers.user_id
        ).filter(
            CompanyMembers.company_id == company_id
        )
        members = await database.fetch_all(members_query)

        query = select(
            Attempts.user_id,
            func.max(Attempts.created_at).label('max_created_at')
        ).filter(
            Attempts.user_id.in_([member['user_id'] for member in members])
        ).group_by(Attempts.user_id)
        records = await database.fetch_all(query)

        return [
            UserTimeResponse(
                user_id=record.user_id,
                created_at=record.max_created_at,
            )
            for record in records
        ]

    def serialize_score_avg(self, stats: Record, ids: dict) -> ScoreAvgResponse:
        return ScoreAvgResponse(
            **ids,
            total_questions=stats.total_questions,
            total_correct_answers=stats.total_correct_answers,
            avg_score=stats.avg_score
        )


analytics_service = AnalyticsService()
