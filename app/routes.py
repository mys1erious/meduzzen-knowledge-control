from fastapi import APIRouter

from app.core.routes import router as core_router
from app.users.routes import router as users_router


router = APIRouter()

router.include_router(core_router)
router.include_router(users_router)
