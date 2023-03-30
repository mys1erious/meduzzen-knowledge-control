from datetime import datetime

from pydantic import BaseModel


class NotificationBaseSchema(BaseModel):
    status: str = None
    text: str = None


class NotificationResponse(NotificationBaseSchema):
    id: int
    created_at: datetime
    created_by: int


class NotificationRequest(NotificationBaseSchema):
    to_user_id: int
