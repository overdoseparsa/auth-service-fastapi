
from typing import Mapping , Optional , List
from .repository import (
    UserRepository,
    ProfileRepository
)

from models.user import User
    
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession , async_sessionmaker



class UserSelector:
    
    """ HINT : 
        why Handel Transation Excutore not in Repository or Session management?  
        - i desisded to prevent that Consequences for Cpu-bound task such as create  
        - validate that query and filters  
        - checking cache and  
        - will be have idle_in_transaction or overtime Session Connection managemanet
    """

    
    def __init__(
        self,
        user_repo:UserRepository,
        profile_repo:ProfileRepository,
        session_factory : async_sessionmaker,
    ):
        self.user_repo = user_repo
        self.profile_repo = profile_repo
        self.session_factory = session_factory


    async def get_user_with_profile(self, user_id , with_profile:bool = True):

        async with self.session_factory() as session :
            async with session.begin():
                user = await self.user_repo.get(session, user_id)
                if not user:
                    return None, None
                if with_profile : 
                    profile = await self.profile_repo.get_by_user_id(session, user_id)
                else : 
                    profile = None 

        return user, profile


    async def get_profile_with_user(self, profile_id , with_user:bool=True):
        
        async with self.session_factory() as session :
            async with session.begin():
                profile = await self.profile_repo.get(session, profile_id)
                if not profile:
                    return None, None

                if with_user:
                    user = await self.user_repo.get(session, profile.user_id)
                else : 
                    user = None

        return profile, user


    

    async def get_all_users(
            self,
            *,
            created_lt,
            created_gt,
            limit,
            offset,
            **filters
            )->Optional[List[User]]:
        


            users_stmt , total_stmt = await self.user_repo.find(
                    session=None ,# just retreive statments
                    created_lt=created_lt,
                    created_gt=created_gt,
                    limit=limit,
                    offset=offset,
                    check_count=True,
                    auto_execute=False,
                    **filters
                )
            


            async with self.session_factory() as session :
                async with session.begin():
                    users = list((await session.execute(users_stmt)).scalars().all())
                    total = await session.scalar(total_stmt)

            return users , total

        

    async def get_all_user_with_profile(
            self,
            *,
            created_lt,
            created_gt,
            limit,
            offset,
            **filters
    ):
        
        """
        for this Case :
        - 1 ): create statmement from users_and_profile (filters,count,validation)
        - 2 ): Open that connection and execute statments
        - 3 ): close Transaction and Release Connection after That
        - 4 ): Serialize data  must must must after transaction Boundery and Connection Release for prevent idle_transaction and OverSession

        in this case
        we can use that :
            - json_agg()
            - json_build_object()

        TODO for serialize and prevent that Lantancy from serializing
        """

        users_with_profile_stmt = await self.user_repo.get_list_user_profile_stmt(
            created_lt = created_lt,
            created_gt=created_gt,
            limit = limit , 
            offset=offset,
            **filters
        )


        async with self.session_factory() as session :
            async with session.begin():
                result =  await session.execute(users_with_profile_stmt)




        users = await self.user_repo._serialize_get_list_user_profile(
            result
        )


        
        return users 


    def __repr__(self):
        return f"{type(self).__name__}(user_repo={self.user_repo!r},profile_repo={self.profile_repo!r})"
    
    def __str__(self):
        return self.__repr__()
    
