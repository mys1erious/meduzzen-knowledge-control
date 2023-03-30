from typing import Literal

from fastapi import APIRouter, Depends
from fastapi_utils.cbv import cbv

from app.core.exceptions import ForbiddenException, ForbiddenHTTPException, NotFoundException, NotFoundHTTPException
from app.users.dependencies import get_current_user
from app.users.schemas import UserResponse

from app.analytics.schemas import ScoreAvgResponse, QuizScoresTimeResponse, QuizTimeResponse, UserScoresTimeResponse
from app.analytics.services import analytics_service


router = APIRouter(tags=['Analytics'])


@cbv(router)
class AnalyticsCBV:
    current_user: UserResponse = Depends(get_current_user)

    @router.get('/my-last-attempts/', response_model=list[QuizTimeResponse])
    async def user_last_attempts(self) -> list[QuizTimeResponse]:
        return await analytics_service.get_user_last_attempts(
            user_id=self.current_user.user_id
        )

    @router.get('/avg-score/', response_model=ScoreAvgResponse, response_model_exclude_unset=True)
    async def score(
            self,
            quiz_id: int = None,
            user_id: int = None,
            company_id: int = None
    ) -> ScoreAvgResponse:
        try:
            return await analytics_service.get_avg_score(
                current_user_id=self.current_user.user_id,
                quiz_id=quiz_id,
                user_id=user_id,
                company_id=company_id
            )
        except ForbiddenException as e:
            raise ForbiddenHTTPException(str(e))
        except NotFoundException as e:
            raise NotFoundHTTPException(str(e))

    @router.get('/avg-scores-by-time/', response_model=list[QuizScoresTimeResponse])
    async def user_avg_scores_by_time(
            self,
            user: int | Literal['me'] = None,
            company_id: int = None
    ) -> list[QuizScoresTimeResponse]:
        if not user or user == 'me':
            user = self.current_user.user_id

        try:
            return await analytics_service.get_user_avg_scores_by_time(
                current_user_id=self.current_user.user_id,
                company_id=company_id,
                user_id=user
            )
        except ForbiddenException as e:
            raise ForbiddenHTTPException(str(e))

    @router.get('/members-avg-scores-by-time/', response_model=list[UserScoresTimeResponse])
    async def members_avg_scores_by_time(self, company_id: int) -> UserScoresTimeResponse:
        try:
            return await analytics_service.get_members_avg_scores_by_time(
                current_user_id=self.current_user.user_id,
                company_id=company_id
            )
        except ForbiddenException as e:
            raise ForbiddenHTTPException(str(e))

    @router.get('/members-last-attempt/')
    async def members_last_attempts(self, company_id: int):
        try:
            return await analytics_service.get_members_last_attempt(
                company_id=company_id,
                current_user_id=self.current_user.user_id
            )
        except ForbiddenException as e:
            raise ForbiddenHTTPException(str(e))
