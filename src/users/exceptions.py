from core.base.expections import CustomException


class DatabaseOperationError(CustomException):
    pass


class DatabaseUnavailableError(CustomException):
    pass


class InternalServiceError(CustomException):
    pass


class TokenGenerationError(CustomException):
    pass


class HashingFailedError(CustomException):
    pass


class UserNotExists(CustomException):
    pass


class EmailAlreadyExists(CustomException):
    pass


class UsernameAlreadyExists(CustomException):
    pass


class UserNotFound(CustomException):
    pass


class SystemDepnedencyError(Exception):
    pass


class ConcurrencyError(Exception):
    pass
