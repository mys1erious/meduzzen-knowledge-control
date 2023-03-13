from pydantic import BaseModel


class InvitationBaseSchema(BaseModel):
    invite_message: str = ''


class SendInvitationRequest(InvitationBaseSchema):
    to_user_id: int
    from_company_id: int


class InvitationResponse(InvitationBaseSchema):
    to_user_id: int
    from_company_id: int


class SendJoinRequest(InvitationBaseSchema):
    to_company_id: int


class JoinRequestResponse(InvitationBaseSchema):
    to_company_id: int
    from_user_id: int
