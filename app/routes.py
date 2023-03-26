from fastapi import APIRouter

from app.core.routes import router as core_router
from app.users.routes import auth_router, users_router
from app.companies.routes import \
    base_router as company_base_router, \
    action_router as company_action_router
from app.invitations.routes import invitations_router, requests_router
from app.quizzes.routes import quiz_router, question_router, answer_router, attempt_router
from app.stats.routes import router as stats_router


router = APIRouter()

router.include_router(core_router)

router.include_router(auth_router, prefix='/users')
router.include_router(users_router, prefix='/users')

router.include_router(company_base_router, prefix='/companies')
router.include_router(company_action_router, prefix='/companies')

router.include_router(invitations_router, prefix='/invitations')
router.include_router(requests_router, prefix='/requests')

router.include_router(quiz_router, prefix='/quizzes')
router.include_router(question_router, prefix='/questions')
router.include_router(answer_router, prefix='/answers')
router.include_router(attempt_router, prefix='/attempts')

router.include_router(stats_router, prefix='/stats')
