from core.base.expections import CustomException


class IdempotencyException(CustomException):
    def __init__(self, message: str):
        super().__init__(message)
