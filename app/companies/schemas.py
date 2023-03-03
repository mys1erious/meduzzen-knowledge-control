from pydantic import BaseModel, constr


class CompanyBaseSchema(BaseModel):
    company_name: constr(min_length=1)
    company_description: str = None


class CompanyResponse(CompanyBaseSchema):
    company_id: int
    company_visible: bool = None
    company_owner_id: int


class CompanyListResponse(BaseModel):
    companies: list[CompanyResponse]


class CompanyCreateRequest(CompanyBaseSchema):
    company_visible: bool = True


class CompanyUpdateRequest(CompanyBaseSchema):
    pass
