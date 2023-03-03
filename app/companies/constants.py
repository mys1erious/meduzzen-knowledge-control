class ExceptionDetails:
    COMPANY_NOT_FOUND = 'User not found.'
    COMPANY_WITH_ID_NOT_FOUND = lambda user_id: f"Company with id {user_id} not found."
