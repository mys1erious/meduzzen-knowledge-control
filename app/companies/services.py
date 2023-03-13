from sqlalchemy import insert, select, delete, update, and_

from app.database import database
from app.core.utils import exclude_none
from app.users.schemas import UserListResponse
from app.users.models import Users
from app.users.utils import serialize_user

from .models import Companies, CompanyMembers
from .schemas import CompanyResponse, CompanyCreateRequest, CompanyListResponse, CompanyUpdateRequest
from .utils import serialize_company
from .exceptions import CompanyNotFoundException, NotYourCompanyException
from .constants import ExceptionDetails


class CompanyService:
    async def get_companies(self, user_id: int) -> CompanyListResponse:
        query = select(Companies)
        companies: list[Companies] = await database.fetch_all(query)

        return CompanyListResponse(companies=[
            serialize_company(company=company)
            for company in companies
            if self.is_visible(company=company, user_id=user_id) is True
        ])

    async def create_company(
            self,
            company_data: CompanyCreateRequest,
            owner_id: int
    ) -> CompanyResponse:
        async with database.transaction():
            create_query = insert(Companies).values(
                owner_id=owner_id,
                name=company_data.company_name,
                description=company_data.company_description,
                visible=company_data.company_visible
            ).returning(Companies)
            company: Companies = await database.fetch_one(create_query)

            add_owner_to_members_query = insert(CompanyMembers).values(
                company_id=company.id,
                user_id=owner_id,
                role='owner'
            )
            await database.fetch_one(add_owner_to_members_query)

            return serialize_company(company)

    async def get_company_by_id(self, company_id: int) -> CompanyResponse:
        company = await self._get_db_company_by_id(company_id)
        if company is None:
            raise CompanyNotFoundException(ExceptionDetails.COMPANY_WITH_ID_NOT_FOUND(company_id))
        return serialize_company(company)

    async def update_company(self, company_id: int, company_data: CompanyUpdateRequest) -> CompanyResponse:
        values = exclude_none({
            'name': company_data.company_name,
            'description': company_data.company_description
        })

        query = update(Companies) \
            .where(Companies.id == company_id) \
            .values(**values) \
            .returning(Companies)

        company = await database.fetch_one(query)
        if company is None:
            raise CompanyNotFoundException(ExceptionDetails.COMPANY_WITH_ID_NOT_FOUND(company_id))

        company = serialize_company(company)
        return company

    async def delete_company(self, company_id: int) -> None:
        company = await self._get_db_company_by_id(company_id=company_id)
        if company is None:
            raise CompanyNotFoundException(ExceptionDetails.COMPANY_WITH_ID_NOT_FOUND(company_id))

        async with database.transaction():
            delete_members_query = delete(CompanyMembers).where(CompanyMembers.company_id == company_id)
            await database.fetch_all(delete_members_query)
            delete_company_query = delete(Companies).where(Companies.id == company_id)
            await database.fetch_one(delete_company_query)

    def is_visible(self, company: Companies | CompanyResponse, user_id: int) -> bool:
        if isinstance(company, CompanyResponse):
            condition = company.company_visible or not company.company_visible and company.company_owner_id == user_id
        else:
            condition = company.visible or not company.visible and company.owner_id == user_id

        if condition:
            return True
        return False

    async def get_company_members(self, company_id: int) -> UserListResponse:
        query = select(Users)\
            .join(CompanyMembers, CompanyMembers.user_id == Users.id)\
            .filter(CompanyMembers.company_id == company_id)
        members = await database.fetch_all(query)
        return UserListResponse(users=[
            serialize_user(member)
            for member in members
        ])

    async def kick_company_member(self, company_id: int, member_id: int, current_user_id: int) -> None:
        company = await self._get_db_company_by_id(company_id=company_id)

        if company.owner_id != current_user_id:
            raise NotYourCompanyException(ExceptionDetails.WRONG_COMPANY)

        kick_query = delete(CompanyMembers).where(and_(
            CompanyMembers.company_id == company_id,
            CompanyMembers.user_id == member_id
        ))
        await database.fetch_one(kick_query)

    async def leave_company(self, company_id: int, current_user_id: int) -> None:
        leave_query = delete(CompanyMembers).where(and_(
            CompanyMembers.company_id == company_id,
            CompanyMembers.user_id == current_user_id
        ))
        await database.fetch_one(leave_query)

    async def _get_db_company_by_id(self, company_id: int) -> Companies:
        query = select(Companies).where(Companies.id == company_id)
        return await database.fetch_one(query)


company_service = CompanyService()
