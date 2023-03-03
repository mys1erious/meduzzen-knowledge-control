from sqlalchemy import insert, select, delete, update

from app.database import database
from app.core.utils import exclude_none

from .models import Companies
from .schemas import CompanyResponse, CompanyCreateRequest, CompanyListResponse, CompanyUpdateRequest
from .utils import serialize_company
from .exceptions import CompanyNotFoundException
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
        query = insert(Companies).values(
            owner_id=owner_id,
            name=company_data.company_name,
            description=company_data.company_description,
            visible=company_data.company_visible
        ).returning(Companies)

        company = await database.fetch_one(query)
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
        query = delete(Companies).where(Companies.id == company_id).returning(Companies)
        company = await database.fetch_one(query)
        if company is None:
            raise CompanyNotFoundException(ExceptionDetails.COMPANY_WITH_ID_NOT_FOUND(company_id))

    def is_visible(self, company: Companies | CompanyResponse, user_id: int) -> bool:
        if isinstance(company, CompanyResponse):
            condition = company.company_visible or not company.company_visible and company.company_owner_id == user_id
        else:
            condition = company.visible or not company.visible and company.owner_id == user_id

        if condition:
            return True
        return False

    async def _get_db_company_by_id(self, company_id: int) -> Companies:
        query = select(Companies).where(Companies.id == company_id)
        return await database.fetch_one(query)


company_service = CompanyService()
