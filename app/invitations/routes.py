from fastapi import APIRouter, Depends
from fastapi_utils.cbv import cbv

from app.core.utils import response_with_result_key
from app.core.exceptions import NotFoundHTTPException, ForbiddenHTTPException, BadRequestHTTPException
from app.core.schemas import DetailResponse
from app.core.constants import SuccessDetails
from app.users.dependencies import get_current_user
from app.users.schemas import UserResponse
from app.users.exceptions import UserNotFoundException, UserAlreadyAMemberException
from app.users.constants import ExceptionDetails as UserExceptionDetails
from app.companies.exceptions import CompanyNotFoundException, NotYourCompanyException
from app.companies.constants import ExceptionDetails as CompanyExceptionDetails

from app.invitations.schemas import SendInvitationRequest, InvitationResponse, SendJoinRequest, JoinRequestResponse
from app.invitations.services import invitation_service, join_request_service
from app.invitations.constants import ExceptionDetails
from app.invitations.exceptions import InvitationNotFoundException, NotYourInvitationException, JoinRequestAlreadySentException


invitations_router = APIRouter(tags=['Invitations'])
requests_router = APIRouter(tags=['Join Requests'])


@cbv(invitations_router)
class InvitationsCBV:
    current_user: UserResponse = Depends(get_current_user)

    @invitations_router.post('/', response_model=DetailResponse)
    async def send_invitation(self, data: SendInvitationRequest) -> DetailResponse:
        try:
            await invitation_service.send_invitation(
                current_user_id=self.current_user.user_id,
                data=data
            )
        except UserNotFoundException:
            raise NotFoundHTTPException(UserExceptionDetails.USER_NOT_FOUND)
        except CompanyNotFoundException:
            raise NotFoundHTTPException(CompanyExceptionDetails.COMPANY_NOT_FOUND)
        except NotYourCompanyException:
            raise ForbiddenHTTPException(CompanyExceptionDetails.WRONG_COMPANY)

        return DetailResponse(detail=SuccessDetails.SUCCESS)

    @invitations_router.get('/my/', response_model=list[InvitationResponse])
    async def get_my_invitations(self) -> list[InvitationResponse]:
        return response_with_result_key(
            await invitation_service.get_my_invitations(
                current_user_id=self.current_user.user_id
            )
        )

    @invitations_router.get('/companies/{company_id}/', response_model=list[InvitationResponse])
    async def get_company_invitations(self, company_id: int) -> list[InvitationResponse]:
        try:
            return response_with_result_key(
                await invitation_service.get_company_invitations(
                    current_user_id=self.current_user.user_id,
                    company_id=company_id
                )
            )
        except CompanyNotFoundException:
            raise NotFoundHTTPException(CompanyExceptionDetails.COMPANY_NOT_FOUND)
        except NotYourCompanyException:
            raise ForbiddenHTTPException(CompanyExceptionDetails.WRONG_COMPANY)

    @invitations_router.delete('/{invitation_id}/', response_model=DetailResponse)
    async def cancel_invitation(self, invitation_id: int) -> DetailResponse:
        try:
            await invitation_service.cancel_invitation(
                invitation_id=invitation_id,
                current_user_id=self.current_user.user_id
            )
        except InvitationNotFoundException:
            raise NotFoundHTTPException(ExceptionDetails.INVITATION_NOT_FOUND)
        except NotYourCompanyException:
            raise ForbiddenHTTPException(CompanyExceptionDetails.WRONG_COMPANY)

        return DetailResponse(detail=SuccessDetails.SUCCESS)

    @invitations_router.get('/{invitation_id}/accept/', response_model=DetailResponse)
    async def accept_invitation(self, invitation_id: int) -> DetailResponse:
        try:
            await invitation_service.accept_invitation(
                invitation_id=invitation_id,
                current_user_id=self.current_user.user_id
            )
        except InvitationNotFoundException:
            raise NotFoundHTTPException(ExceptionDetails.INVITATION_NOT_FOUND)
        except NotYourInvitationException:
            raise ForbiddenHTTPException(ExceptionDetails.WRONG_INVITATION)
        return DetailResponse(detail=SuccessDetails.SUCCESS)

    @invitations_router.get('/{invitation_id}/decline/', response_model=DetailResponse)
    async def decline_invitation(self, invitation_id: int) -> DetailResponse:
        try:
            await invitation_service.decline_invitation(
                invitation_id=invitation_id,
                current_user_id=self.current_user.user_id
            )
        except InvitationNotFoundException:
            raise NotFoundHTTPException(ExceptionDetails.INVITATION_NOT_FOUND)
        except NotYourInvitationException:
            raise ForbiddenHTTPException('User does not have an invite to the company')
        return DetailResponse(detail=SuccessDetails.SUCCESS)


@cbv(requests_router)
class JoinRequestsCBV:
    current_user: UserResponse = Depends(get_current_user)

    @requests_router.post('/', response_model=DetailResponse)
    async def send_join_request(self, data: SendJoinRequest) -> DetailResponse:
        try:
            await join_request_service.send_join_request(
                current_user_id=self.current_user.user_id,
                data=data
            )
        except CompanyNotFoundException:
            raise NotFoundHTTPException(CompanyExceptionDetails.COMPANY_NOT_FOUND)
        except JoinRequestAlreadySentException:
            raise BadRequestHTTPException(ExceptionDetails.REQUEST_ALREADY_SENT)

        except UserAlreadyAMemberException:
            raise BadRequestHTTPException(UserExceptionDetails.USER_ALREADY_A_MEMBER)

        return DetailResponse(detail=SuccessDetails.SUCCESS)

    @requests_router.get('/my/', response_model=list[JoinRequestResponse])
    async def get_my_join_requests(self) -> list[JoinRequestResponse]:
        return response_with_result_key(
            await join_request_service.get_my_join_requests(
                current_user_id=self.current_user.user_id
            )
        )

    @requests_router.get('/companies/{company_id}/', response_model=list[JoinRequestResponse])
    async def get_company_join_requests(self, company_id: int) -> list[JoinRequestResponse]:
        try:
            return response_with_result_key(
                await join_request_service.get_company_join_requests(
                    current_user_id=self.current_user.user_id,
                    company_id=company_id
                )
            )
        except CompanyNotFoundException:
            raise NotFoundHTTPException(CompanyExceptionDetails.COMPANY_NOT_FOUND)
        except NotYourCompanyException:
            raise ForbiddenHTTPException(CompanyExceptionDetails.WRONG_COMPANY)

    @requests_router.delete('/{request_id}/', response_model=DetailResponse)
    async def cancel_join_request(self, request_id: int) -> DetailResponse:
        try:
            await join_request_service.cancel_join_request(
                request_id=request_id,
                current_user_id=self.current_user.user_id
            )
        except InvitationNotFoundException:
            raise NotFoundHTTPException(ExceptionDetails.JOIN_REQUEST_NOT_FOUND)
        except NotYourInvitationException:
            raise ForbiddenHTTPException(ExceptionDetails.WRONG_REQUEST)

        return DetailResponse(detail=SuccessDetails.SUCCESS)

    @requests_router.get('/{request_id}/accept/', response_model=DetailResponse)
    async def accept_join_request(self, request_id: int) -> DetailResponse:
        try:
            await join_request_service.accept_join_request(
                request_id=request_id,
                current_user_id=self.current_user.user_id
            )
        except InvitationNotFoundException:
            raise NotFoundHTTPException(ExceptionDetails.JOIN_REQUEST_NOT_FOUND)
        except NotYourInvitationException:
            raise ForbiddenHTTPException('Only the owner of the company can accept requests')
        return DetailResponse(detail=SuccessDetails.SUCCESS)

    @requests_router.get('/{request_id}/decline/', response_model=DetailResponse)
    async def decline_join_request(self, request_id: int) -> DetailResponse:
        try:
            await join_request_service.decline_join_request(
                request_id=request_id,
                current_user_id=self.current_user.user_id
            )
        except InvitationNotFoundException:
            raise NotFoundHTTPException(ExceptionDetails.JOIN_REQUEST_NOT_FOUND)
        except NotYourInvitationException:
            raise ForbiddenHTTPException('Only the owner of the company can decline requests')
        return DetailResponse(detail=SuccessDetails.SUCCESS)
