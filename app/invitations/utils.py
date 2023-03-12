from .models import Invitations
from .schemas import InvitationResponse, JoinRequestResponse


def serialize_invitation(invitation: Invitations) -> InvitationResponse:
    return InvitationResponse(
        to_user_id=invitation.user_id,
        from_company_id=invitation.company_id,
        invite_message=invitation.message
    )


def serializer_join_request(request: Invitations) -> JoinRequestResponse:
    return JoinRequestResponse(
        from_user_id=request.user_id,
        to_company_id=request.company_id,
        invite_message=request.message
    )
