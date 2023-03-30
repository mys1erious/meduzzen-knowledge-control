from sqlalchemy import select, update, insert, and_

from app.companies.models import CompanyMembers
from app.core.constants import ExceptionDetails, SuccessDetails
from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.schemas import DetailResponse
from app.database import database
from app.logging import file_logger
from app.notifications.constants import Statuses, ON_QUIZ_CREATED_TEXT
from app.notifications.models import Notifications
from app.notifications.schemas import NotificationResponse, NotificationRequest


class NotificationService:
    async def get_my_notifications(self, current_user_id: int, seen=False) -> list[NotificationResponse]:
        query = select(Notifications).filter(
            Notifications.to_user_id == current_user_id,
        )
        if not seen:
            query = query.filter(Notifications.status != Statuses.SEEN)
        notifications = await database.fetch_all(query)

        return [
            self.serialize_notification(notification)
            for notification in notifications
        ]

    async def on_quiz_create_send_notification_to_all_company_members(
            self,
            quiz_id: int,
            company_id: int,
            current_user_id: int
    ) -> DetailResponse:
        query = select(CompanyMembers).filter(
            CompanyMembers.company_id == company_id
        )
        members = await database.fetch_all(query)

        values = []
        for member in members:
            values.append({
                'status': Statuses.SENT,
                'text': ON_QUIZ_CREATED_TEXT(quiz_id),
                'to_user_id': member.user_id,
                'created_by': current_user_id,
                'updated_by': current_user_id
            })

        query = insert(Notifications).values(
            values
        ).returning(Notifications)
        notification = await database.fetch_all(query)

        if not notification:
            file_logger.error(f'send_notification_on_quiz_create error --> values: {values}')

        return DetailResponse(
            detail=SuccessDetails.SUCCESS if notification
            else ExceptionDetails.SOMETHING_WENT_WRONG
        )

    async def get_notification(self, current_user_id: int, notification_id: int) -> NotificationResponse:
        select_query = select(
            Notifications.to_user_id
        ).filter(
            Notifications.id == notification_id
        )
        notification: Notifications = await database.fetch_one(select_query)

        if not notification:
            raise NotFoundException(ExceptionDetails.NOT_FOUND)
        if notification.to_user_id != current_user_id:
            raise ForbiddenException(ExceptionDetails.NOT_ALLOWED)

        update_query = update(Notifications).where(
            Notifications.id == notification_id
        ).values(
            status=Statuses.SEEN
        ).returning(Notifications)
        notification = await database.fetch_one(update_query)

        return self.serialize_notification(notification)

    def serialize_notification(self, notification: Notifications) -> NotificationResponse:
        return NotificationResponse(
            id=notification.id,
            status=notification.status,
            text=notification.text,
            created_at=notification.created_at,
            created_by=notification.created_by
        )


notification_service = NotificationService()
