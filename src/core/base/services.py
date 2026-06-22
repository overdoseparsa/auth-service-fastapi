from abc import ABC

class BaseAbstractService(ABC):
    service_name: str = "base_service" 
    
    """
    SERVICE LAYER GUIDELINES (Production-Grade):
    -------------------------------------------
    To prevent 'idle_in_transaction' and connection pool exhaustion:

    1. [PRE-PROCESS]: Do all CPU-bound or external IO tasks (hashing, API calls, validations) 
       BEFORE opening a database transaction.
    
    2. [DB-PROCESS]: Keep the 'async with session.begin():' block extremely tight. 
       Execute ONLY database queries. Never 'await' long-running non-DB tasks inside.
    
    3. [AFTER-PROCESS]: Post-commit actions (sending emails, cache invalidation, 
       triggering background tasks) must execute AFTER the transaction is closed.
    """

    def __init__(self):
        if type(self) is BaseAbstractService:
            raise TypeError("BaseAbstractService cannot be instantiated directly.")

    def __str__(self) -> str:
        return self.service_name
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.service_name}')>"



    