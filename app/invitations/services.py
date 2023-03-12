from sqlalchemy import insert, select, delete, and_

from app.database import database
from app.users.exceptions import UserNotFoundException, UserAlreadyAMemberException
from app.users.constants import ExceptionDetails as UserExceptionDetails
from app.users.services import user_service
from app.companies.exceptions import CompanyNotFoundException, NotYourCompanyException
from app.companies.constants import ExceptionDetails as CompanyExceptionDetails
from app.companies.services import company_service
from app.companies.models import CompanyMembers

from .models import Invitations
from .schemas import SendInvitationRequest, InvitationResponse, SendJoinRequest, JoinRequestResponse
from .utils import serialize_invitation, serializer_join_request
from .constants import ExceptionDetails
from .exceptions import InvitationNotFoundException, NotYourInvitationException, JoinRequestAlreadySentException


class InvitationService:
    async def send_invitation(self, data: SendInvitationRequest, current_user_id: int) -> InvitationResponse:
        user = await user_service.get_user_by_id(user_id=data.to_user_id)
        if not user:
            raise UserNotFoundException(UserExceptionDetails.USER_NOT_FOUND)

        company = await company_service.get_company_by_id(company_id=data.from_company_id)
        if not company:
            raise CompanyNotFoundException(CompanyExceptionDetails.COMPANY_NOT_FOUND)

        if current_user_id != company.company_owner_id:
            raise NotYourCompanyException(CompanyExceptionDetails.WRONG_COMPANY)

        query = insert(Invitations).values(
            user_id=data.to_user_id,
            company_id=data.from_company_id,
            message=data.invite_message,
            type='invitation'
        ).returning(Invitations)
        invitation = await database.fetch_one(query)
        return serialize_invitation(invitation=invitation)

    async def get_my_invitations(self, current_user_id: int) -> list[InvitationResponse]:
        query = select(Invitations).where(and_(
            Invitations.user_id == current_user_id,
            Invitations.type == 'invitation',
        ))
        invitations = await database.fetch_all(query)
        return [
            serialize_invitation(invitation=invitation)
            for invitation in invitations
        ]

    async def get_company_invitations(self, current_user_id: int, company_id: int) -> list[InvitationResponse]:
        company = await company_service.get_company_by_id(company_id=company_id)
        if not company:
            raise CompanyNotFoundException(CompanyExceptionDetails.COMPANY_NOT_FOUND)

        if current_user_id != company.company_owner_id:
            raise NotYourCompanyException(CompanyExceptionDetails.WRONG_COMPANY)

        query = select(Invitations).where(and_(
            Invitations.company_id == company_id,
            Invitations.type == 'invitation'
        ))
        invitations = await database.fetch_all(query)
        return [
            serialize_invitation(invitation=invitation)
            for invitation in invitations
        ]

    async def cancel_invitation(self, invitation_id: int, current_user_id: int) -> None:
        invitation = await self.get_invitation_by_id(invitation_id=invitation_id)

        company = await company_service.get_company_by_id(company_id=invitation.from_company_id)
        if company.company_owner_id != current_user_id:
            raise NotYourCompanyException(CompanyExceptionDetails.WRONG_COMPANY)

        query = delete(Invitations).where(Invitations.id == invitation_id)
        await database.fetch_one(query)

    async def get_invitation_by_id(self, invitation_id: int) -> InvitationResponse:
        query = select(Invitations).where(Invitations.id == invitation_id)
        invitation = await database.fetch_one(query)
        if invitation is None:
            raise InvitationNotFoundException(ExceptionDetails.INVITATION_NOT_FOUND)
        return serialize_invitation(invitation)

    async def accept_invitation(self, invitation_id: int, current_user_id: int) -> None:
        invitation = await self.get_invitation_by_id(invitation_id=invitation_id)
        if invitation.to_user_id != current_user_id:
            raise NotYourInvitationException(ExceptionDetails.WRONG_INVITATION)

        async with database.transaction():
            add_to_members_query = insert(CompanyMembers).values(
                company_id=invitation.from_company_id,
                user_id=current_user_id
            )
            await database.fetch_one(add_to_members_query)

            delete_invitation_query = delete(Invitations)\
                .where(Invitations.id == invitation_id)\
                .returning(Invitations)
            await database.fetch_one(delete_invitation_query)

    async def decline_invitation(self, invitation_id: int, current_user_id: int) -> None:
        invitation = await self.get_invitation_by_id(invitation_id=invitation_id)
        if invitation.to_user_id != current_user_id:
            raise NotYourInvitationException(ExceptionDetails.WRONG_INVITATION)

        query = delete(Invitations).where(Invitations.id == invitation_id).returning(Invitations)
        await database.fetch_one(query)


class JoinRequestService:
    async def send_join_request(self, data: SendJoinRequest, current_user_id: int) -> JoinRequestResponse:
        company = await company_service.get_company_by_id(company_id=data.to_company_id)
        if not company:
            raise CompanyNotFoundException(CompanyExceptionDetails.COMPANY_NOT_FOUND)

        join_request_query = select(Invitations) \
            .where(and_(
                Invitations.user_id == current_user_id,
                Invitations.company_id == data.to_company_id,
                Invitations.type == 'join_request'
            ))
        join_request = await database.fetch_one(join_request_query)
        if join_request:
            raise JoinRequestAlreadySentException(ExceptionDetails.REQUEST_ALREADY_SENT)

        member_ids_query = select(CompanyMembers.user_id)\
            .where(CompanyMembers.company_id == company.company_id)
        member_ids = await database.fetch_all(member_ids_query)

        if current_user_id in [member_id[0] for member_id in member_ids]:
            raise UserAlreadyAMemberException(UserExceptionDetails.USER_ALREADY_A_MEMBER)

        send_query = insert(Invitations).values(
            user_id=current_user_id,
            company_id=data.to_company_id,
            message=data.invite_message,
            type='join_request'
        ).returning(Invitations)
        join_request = await database.fetch_one(send_query)
        return serializer_join_request(request=join_request)

    async def get_my_join_requests(self, current_user_id: int) -> list[JoinRequestResponse]:
        query = select(Invitations).where(and_(
            Invitations.user_id == current_user_id,
            Invitations.type == 'join_request',
        ))
        join_requests = await database.fetch_all(query)
        return [
            serializer_join_request(request=request)
            for request in join_requests
        ]

    async def get_company_join_requests(self, current_user_id: int, company_id: int) -> list[JoinRequestResponse]:
        company = await company_service.get_company_by_id(company_id=company_id)
        if not company:
            raise CompanyNotFoundException(CompanyExceptionDetails.COMPANY_NOT_FOUND)

        if current_user_id != company.company_owner_id:
            raise NotYourCompanyException(CompanyExceptionDetails.WRONG_COMPANY)

        query = select(Invitations).where(and_(
            Invitations.company_id == company_id,
            Invitations.type == 'join_request'
        ))
        join_requests = await database.fetch_all(query)
        return [
            serializer_join_request(request=request)
            for request in join_requests
        ]

    async def cancel_join_request(self, request_id: int, current_user_id: int) -> None:
        request = await self.get_request_by_id(request_id=request_id)

        if request.from_user_id != current_user_id:
            raise NotYourInvitationException(ExceptionDetails.WRONG_REQUEST)

        query = delete(Invitations).where(Invitations.id == request_id)
        await database.fetch_one(query)

    async def get_request_by_id(self, request_id: int) -> JoinRequestResponse:
        query = select(Invitations).where(Invitations.id == request_id)
        request = await database.fetch_one(query)
        if request is None:
            raise InvitationNotFoundException(ExceptionDetails.JOIN_REQUEST_NOT_FOUND)
        return serializer_join_request(request=request)

    async def accept_join_request(self, request_id: int, current_user_id: int) -> None:
        request = await self.get_request_by_id(request_id=request_id)
        company = await company_service.get_company_by_id(company_id=request.to_company_id)

        if current_user_id != company.company_owner_id:
            raise NotYourInvitationException(ExceptionDetails.WRONG_INVITATION)

        async with database.transaction():
            add_to_members_query = insert(CompanyMembers).values(
                company_id=request.to_company_id,
                user_id=request.from_user_id
            )
            await database.fetch_one(add_to_members_query)

            delete_invitation_query = delete(Invitations)\
                .where(Invitations.id == request_id)
            await database.fetch_one(delete_invitation_query)

    async def decline_join_request(self, request_id: int, current_user_id: int) -> None:
        request = await self.get_request_by_id(request_id=request_id)
        company = await company_service.get_company_by_id(company_id=request.to_company_id)

        if current_user_id != company.company_owner_id:
            raise NotYourInvitationException(ExceptionDetails.WRONG_INVITATION)

        query = delete(Invitations).where(Invitations.id == request_id)
        await database.fetch_one(query)


invitation_service = InvitationService()
join_request_service = JoinRequestService()
