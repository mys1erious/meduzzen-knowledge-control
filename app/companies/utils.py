from .models import Companies
from .schemas import CompanyResponse


def serialize_company(company: Companies) -> CompanyResponse:
    company_data = CompanyResponse(
        company_id=company.id,
        company_name=company.name,
        company_description=company.description,
        company_owner_id=company.owner_id,
        company_visible=company.visible
    )

    return company_data
