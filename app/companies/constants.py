class ExceptionDetails:
    COMPANY_NOT_FOUND = 'This company not found'
    COMPANY_WITH_ID_NOT_FOUND = lambda user_id: f"company with id {user_id} not found"
    WRONG_COMPANY = 'it\'s not your company'
