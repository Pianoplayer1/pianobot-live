from logging import getLogger
from typing import Any

from asyncpg import Pool, Record, create_pool


class Connection:
    def __init__(self, database: str, host: str, password: str, user: str) -> None:
        self._database = database
        self._host = host
        self._password = password
        self._user = user
        self._pool: Pool[Record] | None = None

    async def connect(self) -> None:
        self._pool = await create_pool(
            database=self._database,
            host=self._host,
            password=self._password,
            user=self._user,
        )
        getLogger('database').debug('Connected to database %s', self._database)

    async def execute(self, sql: str, *args: Any) -> str:
        if self._pool is None:
            raise AttributeError('Connection not initialized!')
        return await self._pool.execute(sql, *args)

    async def query(self, sql: str, *args: Any) -> list[Record]:
        if self._pool is None:
            raise AttributeError('Connection not initialized!')
        records: list[Record] = await self._pool.fetch(sql, *args)
        return records

    async def disconnect(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            getLogger('database').debug('Disconnected from database %s', self._database)
