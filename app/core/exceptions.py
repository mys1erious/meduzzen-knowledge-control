from fastapi import HTTPException, status


class BadRequestHTTPException(HTTPException):
    def __init__(self, detail='Bad request'):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.detail = detail


class NotFoundHTTPException(HTTPException):
    def __init__(self, detail='Not found'):
        self.status_code = status.HTTP_404_NOT_FOUND
        self.detail = detail


class UnprocessableEntityHTTPException(HTTPException):
    def __init__(self, detail='Unprocessable entity'):
        self.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        self.detail = detail


class UnauthorizedHTTPException(HTTPException):
    def __init__(self, detail='Unauthorized'):
        self.status_code = status.HTTP_401_UNAUTHORIZED
        self.detail = detail
        self.headers = {"WWW-Authenticate": "Bearer"}
