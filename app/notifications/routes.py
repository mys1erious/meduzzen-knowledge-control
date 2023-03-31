from fastapi import APIRouter, Depends
from fastapi_utils.cbv import cbv

from app.core.exceptions import NotFoundException, NotFoundHTTPException, ForbiddenHTTPException, ForbiddenException
from app.core.schemas import DetailResponse
from app.notifications.schemas import NotificationResponse, NotificationRequest
from app.notifications.services import notification_service
from app.users.dependencies import get_current_user
from app.users.schemas import UserResponse


router = APIRouter(tags=['Notifications'])


@cbv(router)
class CompaniesCBV:
    current_user: UserResponse = Depends(get_current_user)

    @router.get('/my/', response_model=list[NotificationResponse])
    async def my_notifications(self, seen: bool = False) -> list[NotificationResponse]:
        return await notification_service.get_my_notifications(
            current_user_id=self.current_user.user_id,
            seen=seen
        )

    @router.get('/{notification_id}/', response_model=NotificationResponse)
    async def get_notification(self, notification_id: int) -> NotificationResponse:
        try:
            return await notification_service.get_notification(
                current_user_id=self.current_user.user_id,
                notification_id=notification_id
            )
        except NotFoundException as e:
            raise NotFoundHTTPException(str(e))
        except ForbiddenException as e:
            raise ForbiddenHTTPException(str(e))
