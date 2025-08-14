from __future__ import annotations

import asyncio
import contextlib
import uuid
from datetime import datetime
from typing import Any
from typing import AsyncGenerator
from typing import Optional
from typing import Self
from typing import Union
from zoneinfo import ZoneInfo

import pendulum
import sqlalchemy as sa
from sqlalchemy import Select
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects import sqlite
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_scoped_session
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.sql import elements
from sqlalchemy.sql import functions
from sqlalchemy.sql.compiler import SQLCompiler
from sqlalchemy.sql.dml import ValuesBase
from sqlalchemy.types import CHAR
from sqlalchemy.types import TypeDecorator
from sqlalchemy.types import TypeEngine

SQLALCHEMY_DATABASE_URI = 'sqlite+aiosqlite:///db.sqlite3'

engine = create_async_engine(SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)

session_function = async_sessionmaker(engine, autoflush=False, expire_on_commit=False)

Session = async_scoped_session(session_function, scopefunc=asyncio.current_task)


@contextlib.asynccontextmanager
async def create_session() -> AsyncGenerator[AsyncSession, None]:
    session = Session()
    try:
        yield session
        await session.rollback()
    except:
        await session.rollback()
        raise
    finally:
        await session.close()


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(
            BaseModel.metadata.create_all,
            tables=[
                RssPostHistory.__table__,
            ],
        )


async def drop_tables():
    async with engine.begin() as conn:
        await conn.run_sync(
            BaseModel.metadata.drop_all,
            tables=[
                RssPostHistory.__table__,
            ],
        )


def upsert(table):
    return Upsert(table)


class Upsert(ValuesBase):
    inherit_cache = True

    def __init__(self, table):
        ValuesBase.__init__(self, table)
        self._returning = None
        self._inline = None

    @property
    def columns(self):
        return self.table.columns

    @property
    def pk_columns(self):
        return [c for c in self.table.columns if c.primary_key]

    @property
    def non_pk_columns(self):
        return [c for c in self.table.columns if not c.primary_key]

    def values(self, compiler):
        return [self._create_bind_param(compiler, c) for c in self.table.columns]

    def _create_bind_param(self, compiler, col, process=True):
        bindparam = elements.BindParameter(col.key, type_=col.type, required=True)
        bindparam._is_crud = True
        bindparam = bindparam._compiler_dispatch(compiler)
        return bindparam


@compiles(Upsert, 'sqlite')
def compile_upsert_sqlite(upsert_stmt, compiler, **kwargs):
    # See https://sqlite.org/lang_insert.html
    insert_stmt = upsert_stmt.table.insert().prefix_with('OR REPLACE')
    return compiler.process(insert_stmt)


@compiles(Upsert, 'postgresql')
def compile_upsert_postgresql(upsert_stmt, compiler, **kwargs):
    # See https://docs.sqlalchemy.org/en/14/dialects/postgresql.html#insert-on-conflict-upsert
    insert_stmt = postgresql.insert(upsert_stmt.table)
    pk_col_names = [c.name for c in upsert_stmt.pk_columns]
    update_dict = {c.name: c for c in insert_stmt.excluded if c.name not in pk_col_names}
    insert_stmt = insert_stmt.on_conflict_do_update(index_elements=pk_col_names, set_=update_dict)
    return compiler.process(insert_stmt)


class GenerateUUID(functions.FunctionElement[uuid.UUID]):
    name = 'uuid_default'


@compiles(GenerateUUID, 'postgresql')
def generate_uuid_postgresql(element: GenerateUUID, compiler: SQLCompiler, **kwargs: Any) -> str:
    return '(GEN_RANDOM_UUID())'


@compiles(GenerateUUID, 'sqlite')
def generate_uuid_sqlite(element: GenerateUUID, compiler: SQLCompiler, **kwargs: Any) -> str:
    return """
    (
        lower(hex(randomblob(4)))
        || '-'
        || lower(hex(randomblob(2)))
        || '-4'
        || substr(lower(hex(randomblob(2))),2)
        || '-'
        || substr('89ab',abs(random()) % 4 + 1, 1)
        || substr(lower(hex(randomblob(2))),2)
        || '-'
        || lower(hex(randomblob(6)))
    )
    """


class Timestamp(TypeDecorator[datetime]):
    impl: TypeEngine[Any] | type[TypeEngine[Any]] = sa.TIMESTAMP(timezone=True)
    cache_ok: bool | None = True

    def load_dialect_impl(self, dialect: sa.Dialect) -> TypeEngine[Any]:
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(postgresql.TIMESTAMP(timezone=True))
        elif dialect.name == 'sqlite':
            return dialect.type_descriptor(sqlite.DATETIME())
        else:
            return dialect.type_descriptor(sa.TIMESTAMP(timezone=True))

    def process_bind_param(
        self,
        value: Optional[datetime],
        dialect: sa.Dialect,
    ) -> Optional[datetime]:
        if value is None:
            return None
        else:
            if value.tzinfo is None:
                raise ValueError('Timestamps must have a timezone.')
            elif dialect.name == 'sqlite':
                return value.astimezone(ZoneInfo('UTC'))
            else:
                return value

    def process_result_value(
        self,
        value: Optional[datetime],
        dialect: sa.Dialect,
    ) -> Optional[datetime]:
        # retrieve timestamps in their native timezone (or UTC)
        if value is not None:
            if value.tzinfo is None:
                return value.replace(tzinfo=ZoneInfo('UTC'))
            else:
                return value.astimezone(ZoneInfo('UTC'))


class UUID(TypeDecorator[uuid.UUID]):
    impl: type[TypeEngine[Any]] | TypeEngine[Any] = TypeEngine
    cache_ok: bool | None = True

    def load_dialect_impl(self, dialect: sa.Dialect) -> TypeEngine[Any]:
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(postgresql.UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value: Optional[Union[str, uuid.UUID]], dialect: sa.Dialect) -> Optional[str]:
        if value is None:
            return None
        elif dialect.name == 'postgresql':
            return str(value)
        elif isinstance(value, uuid.UUID):
            return str(value)
        else:
            return str(uuid.UUID(value))

    def process_result_value(self, value: Optional[Union[str, uuid.UUID]], dialect: sa.Dialect) -> Optional[uuid.UUID]:
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value


class BaseModel(DeclarativeBase):
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        primary_key=True,
        server_default=GenerateUUID(),
        default=uuid.uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(
        Timestamp(),
        nullable=False,
        default=lambda: pendulum.now(),
        server_default=func.current_timestamp(),
    )
    updated_at: Mapped[Timestamp] = mapped_column(
        Timestamp(),
        nullable=False,
        default=lambda: pendulum.now('UTC'),
        server_default=func.current_timestamp(),
        onupdate=lambda: pendulum.now('UTC'),
        server_onupdate=func.current_timestamp(),
    )

    @classmethod
    def build_query(
        cls,
        *where,
        order_by: list | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> Select:
        query = select(cls)
        if where:
            query = query.where(*where)
        if order_by:
            query = query.order_by(*order_by)
        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        return query

    @classmethod
    async def get_list(
        cls,
        *where,
        order_by: list | None = None,
        offset: int | None = None,
        limit: int | None = None,
        session: AsyncSession = None,
    ) -> list[Self]:
        async with session or Session() as session:
            filters = list(where)
            query = cls.build_query(*filters, order_by=order_by, offset=offset, limit=limit)
            result = await session.scalars(query)
            return list(result)

    @classmethod
    async def count(cls, *where, session: AsyncSession = None) -> int:
        async with session or Session() as session:
            subquery = cls.build_query(*where).subquery()
            query = select(func.count(subquery.c.id).label('count'))
            result = await session.execute(query)
            for (count,) in result:
                return count
        return 0


class RssPostHistory(BaseModel):
    __tablename__ = 'rss_post_history'
    post_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True, unique=True)
    url: Mapped[str] = mapped_column(String(256), nullable=False, index=True, unique=True)
    author: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    tag: Mapped[str] = mapped_column(String(32), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime] = mapped_column(
        Timestamp(),
        nullable=False,
        default=lambda: pendulum.now('UTC'),
        index=True,
    )

    @classmethod
    async def get_list_by_page(
        cls,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
        session: AsyncSession = None,
    ) -> tuple[list[Self], int]:
        where = []
        if start_time:
            where.append(cls.published_at >= start_time)
        if end_time:
            where.append(cls.published_at < end_time)
        async with session or Session() as session:
            posts = await cls.get_list(
                *where,
                order_by=[cls.published_at.desc()],
                offset=(page - 1) * page_size,
                limit=page_size,
                session=session,
            )
            total_count = await cls.count(
                *where,
                session=session,
            )
            return posts, total_count
