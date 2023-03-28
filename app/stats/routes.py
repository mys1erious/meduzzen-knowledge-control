from fastapi import APIRouter, Depends
from fastapi_utils.cbv import cbv

from app.core.exceptions import ForbiddenException, ForbiddenHTTPException, NotFoundException, NotFoundHTTPException
from app.users.dependencies import get_current_user
from app.users.schemas import UserResponse
from app.quizzes.schemas import QuizStatsResponse
from app.quizzes.services import quiz_service


router = APIRouter(tags=['Stats'])


@cbv(router)
class StatsCBV:
    current_user: UserResponse = Depends(get_current_user)

    @router.get('/avg-score/', response_model=QuizStatsResponse, response_model_exclude_unset=True)
    async def avg(
            self,
            quiz_id: int = None,
            user_id: int = None,
            company_id: int = None
    ) -> QuizStatsResponse:
        try:
            return await quiz_service.get_quiz_stats(
                current_user_id=self.current_user.user_id,
                quiz_id=quiz_id,
                user_id=user_id,
                company_id=company_id
            )
        except ForbiddenException as e:
            raise ForbiddenHTTPException(str(e))
        except NotFoundException as e:
            raise NotFoundHTTPException(str(e))
