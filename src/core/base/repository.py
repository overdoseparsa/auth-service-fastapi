from datetime import datetime
from functools import lru_cache
from typing import (
    Any,
    Generic,
    Mapping,
    Optional,
    Type,
    TypeVar,
)

from sqlalchemy import (
    Select,
    exists,
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.inspection import inspect

from infrastructure.sqlalchemy.base import CustomBase as base

from .expections import NotFoundException

T = TypeVar("T", bound=base)


class BaseRepository(Generic[T]):
    @staticmethod
    @lru_cache(maxsize=32)
    def get_the_valid_fields(model):

        mapper = inspect(model)
        return {key for key in mapper.all_orm_descriptors.keys()}

    def __init__(self, model: Type[T]):
        if model is None:
            raise ValueError("model must not be None")
        self.model = model
        self._valid_columns = BaseRepository.get_the_valid_fields(self.model)

    @staticmethod
    def add_domain_filters(
        stmt: Select,
        model_class: Type[T],
        filters: Mapping[str, Any],
    ) -> Select:

        mapper = inspect(model_class)

        for key, value in filters.items():
            if key not in mapper.columns:
                raise NotFoundException(
                    f"{key} is not a valid column of {model_class.__name__}"
                )

            column = mapper.columns[key]

            stmt = stmt.where(column == value)

        return stmt

    @staticmethod
    def filter_by_timezone(
        stmt: Select,
        created_lt: datetime,
        created_gt: datetime,
        models_class: Type[T],
    ) -> Select:

        stmt_r = stmt

        if created_lt is not None:
            stmt_r = stmt_r.where(models_class.created_at <= created_lt)

        if created_gt is not None:
            stmt_r = stmt_r.where(models_class.created_at >= created_gt)

        return stmt_r

    @staticmethod
    def filter_by_limit_offset(
        stmt: Select,
        limit: int,
        offset: int,
    ) -> Select:

        stmt_r = stmt
        stmt_r = stmt_r.limit(limit).offset(offset)
        return stmt_r

    async def get(self, session: AsyncSession, id: int | str) -> T | None:
        stmt = select(self.model).where(self.model.id == id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, session: AsyncSession, auto_flush=True, **kwargs: Any) -> T:
        invalid_fields = set(kwargs) - self._valid_columns
        if invalid_fields:
            raise NotFoundException(f"invalid fields for {self.model.__name__}")

        obj = self.model(**kwargs)
        session.add(obj)
        if auto_flush:
            await session.flush()
        return obj

    async def delete(self, session: AsyncSession, obj: T) -> None:
        await session.delete(obj)
        await session.flush()

    async def exists(self, session: AsyncSession, **filters: Any) -> bool:
        invalid_fields = set(filters) - self._valid_columns
        if invalid_fields:
            raise NotFoundException(f"invalid fields for {self.model.__name__}")

        conditions = [getattr(self.model, k) == v for k, v in filters.items()]
        stmt = select(exists().where(*conditions))
        result = await session.execute(stmt)
        return bool(result.scalar())

    async def update(
        self,
        session: AsyncSession,
        obj: T,
        **kwargs: Any,
    ) -> T:
        invalid_fields = set(kwargs) - self._valid_columns
        if invalid_fields:
            raise NotFoundException(f"invalid fields for {self.model.__name__}")

        for key, value in kwargs.items():
            setattr(obj, key, value)

        await session.flush()
        return obj

    async def find(
        self,
        session: Optional[AsyncSession],
        *,
        created_lt: datetime | None = None,
        created_gt: datetime | None = None,
        limit: int = 10,
        offset: int = 0,
        check_count: bool = False,
        auto_execute: bool = True,
        **domain_filters,
    ) -> tuple[list[T], int | None]:

        stmt = select(self.model)

        if domain_filters:
            stmt = self.add_domain_filters(stmt, self.model, domain_filters)

        stmt = self.filter_by_timezone(stmt, created_lt, created_gt, self.model)
        stmt = self.filter_by_limit_offset(stmt, limit, offset).order_by(
            self.model.created_at.desc()
        )

        total = None
        if (
            check_count
        ):  # TODO will adding Stats Table / Aggregate Table for each table seprately
            count_stmt = select(func.count()).select_from(self.model)

            count_stmt = self.add_domain_filters(count_stmt, self.model, domain_filters)

            count_stmt = self.filter_by_timezone(
                count_stmt, created_lt, created_gt, self.model
            )

            if auto_execute and session:
                total = await session.scalar(count_stmt)

            else:
                total = count_stmt

        print(
            "session", session, "auht", auto_execute, "bool", (auto_execute and session)
        )
        return (list((await session.execute(stmt)).scalars().all()), total) if (
            auto_execute and session
        ) else stmt, total
