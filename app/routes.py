from fastapi import APIRouter

from app.core.routes import router as core_router
from app.users.routes import auth_router
from app.users.routes import users_router
from app.companies.routes import router as companies_router


router = APIRouter()

router.include_router(core_router)
router.include_router(auth_router, prefix='/users')
router.include_router(users_router, prefix='/users')
router.include_router(companies_router, prefix='/companies')
