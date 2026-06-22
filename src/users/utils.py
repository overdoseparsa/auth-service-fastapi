from sqlalchemy.exc import IntegrityError
from .exceptions import (
    InternalServiceError,
    DatabaseUnavailableError,
    DatabaseOperationError
)

from constract.expections import (
    DuplicateValueException
)

def extract_unique_field(exc) -> str:
    msg = str(exc).lower()
    if "email" in msg:
        return "email"
    if "username" in msg:
        return "username"
    return "unknown"

def service_method_wrapper(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)

        except IntegrityError as exc:

            if "unique" in str(exc).lower():
                raise DuplicateValueException(message=extract_unique_field(exc))

            raise DatabaseOperationError(message=str(exc))

        except ConnectionError:
            raise DatabaseUnavailableError()

        except Exception as exc:
            print(f"[ERROR] Internal service error: {exc}")
            raise InternalServiceError()  

    return wrapper
