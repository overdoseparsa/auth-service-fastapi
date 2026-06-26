from sqlalchemy.ext.asyncio import async_sessionmaker

from .schemas import UserRegister, UserUpdate
from .service import ProfileService, UserService


class UserRegistrationController:
    """

    High‑level orchestrator service responsible for handling the entire
    user onboarding workflow in an atomic and transactional mangner.

    Responsibilities:
        - Create the user account.
        - Create the user's profile (1:1 relationship).
        - (Future) Create a default wallet for the user.
        - (Future) Send a welcome email after successful onboarding.
        - (Future) Emit analytics/telemetry events for user signup.

    This service coordinates multiple domain services (UserService,
    ProfileService, etc.) and ensures that all steps are executed
    within a single database transaction. If any operation fails,
    the transaction is rolled back and the system remains in a
    consistent state.

    """

    def __init__(
        self,
        user_service: UserService,
        profile_service: ProfileService,
        session_factory: async_sessionmaker,
    ):
        self.user_service = user_service
        self.profile_service = profile_service
        self.session_factory = session_factory
        # must have stateless session not provide self.__init__(self,session)

    async def register(self, *, data: UserRegister):
        """
        prevent partial failures (all-or-nothing). Connection is released immediately
        to the pool upon context exit, minimizing idle duration.

        """
        user_fields, token = await self.user_service.pre_create_user_process(data)

        async with (
            self.session_factory() as session
        ):  # Just connection Here for prevent idle_transaction and less session active
            async with session.begin():  # atomic transaction
                user = await self.user_service.db_create_user_process(
                    session, user_fields
                )
                profile = await self.profile_service.db_create_profile_process(
                    session, user
                )

        await self.user_service.after_create_user_process(user)
        await self.profile_service.after_create_profile_process(profile)

        return user, token, profile

    async def update_user(self, user_id: int, data: UserUpdate):
        async with self.session_factory() as session:
            async with session.begin():
                user = await self.user_service.update_user(
                    session=session, user_id=user_id, data=data
                )

            return user
