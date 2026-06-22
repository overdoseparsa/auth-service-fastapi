from http import HTTPStatus
from typing import Optional


class CustomException(Exception):
    code = HTTPStatus.BAD_GATEWAY
    error_code = HTTPStatus.BAD_GATEWAY
    message = HTTPStatus.BAD_GATEWAY.description

    def __init__(self, message: Optional[str] = None, error_code: Optional[str] = None):
        self.message = message or self.message
        self.error_code = error_code or self.error_code
        super().__init__(self.message)


class BadRequestException(CustomException):
    code = HTTPStatus.BAD_REQUEST
    error_code = "BAD_REQUEST"
    message = "Bad request"


class NotFoundException(CustomException):
    code = HTTPStatus.NOT_FOUND
    error_code = "NOT_FOUND"
    message = "Resource not found"


class ForbiddenException(CustomException):
    code = HTTPStatus.FORBIDDEN
    error_code = "FORBIDDEN"
    message = "Access forbidden"


class UnauthorizedException(CustomException):
    code = HTTPStatus.UNAUTHORIZED
    error_code = "UNAUTHORIZED"
    message = "Authentication required"


class UnprocessableEntity(CustomException):
    code = HTTPStatus.UNPROCESSABLE_ENTITY
    error_code = "VALIDATION_ERROR"
    message = "Validation failed"


class DuplicateValueException(CustomException):
    code = HTTPStatus.CONFLICT 
    error_code = "DUPLICATE_VALUE"
    message = "Duplicate value found"

