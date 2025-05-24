from datetime import datetime

from asyncpg import Record

from pianobot.db import Connection
from pianobot.utils import get_rounded_time


class GuildXP:
    def __init__(self, time: datetime, data: dict[str, int | None]) -> None:
        self._time = time
        self._data = data

    @property
    def time(self) -> datetime:
        return self._time

    @property
    def data(self) -> dict[str, int | None]:
        return self._data


class GuildXPTable:
    def __init__(self, con: Connection) -> None:
        self._con = con

    async def get_members(self) -> list[str]:
        result = await self._con.query(
            'SELECT column_name FROM information_schema.columns WHERE table_name = \'guild_xp\''
        )
        return [] if len(result) <= 1 else [column[0] for column in result[1:]]

    async def get(self, time: datetime) -> GuildXP | None:
        return await self._bind(
            await self._con.query('SELECT * FROM guild_xp WHERE time =$1', time)
        )

    async def get_first(self, interval: str) -> GuildXP | None:
        return await self._bind(
            await self._con.query(
                'SELECT * FROM guild_xp WHERE time > (CURRENT_TIMESTAMP -'
                f' \'{interval}\'::interval) ORDER BY time LIMIT 1'
            )
        )

    async def get_between(self, start: datetime | None = None, end: datetime | None = None) -> dict[str, int]:
        members = await self.get_members()
        result_start = await self._con.query(
            'SELECT * FROM guild_xp WHERE time >= $1 ORDER BY time LIMIT 1',
            start or datetime.min,
        )
        result_end = await self._con.query(
            'SELECT * FROM guild_xp WHERE time <= $1 ORDER BY time DESC LIMIT 1',
            end or datetime.max,
        )
        if len(result_end) + len(result_start) == 0:
            return {}
        start_data = result_start[0]
        end_data = result_end[0]
        return {
            member: (end_data[i + 1] or 0) - (start_data[i + 1] or 0)
            for i, member in enumerate(members)
            if (end_data[i + 1] or 0) - (start_data[i + 1] or 0) > 0
        }

    async def _bind(self, result: list[Record]) -> GuildXP | None:
        members = await self.get_members()
        if result:
            row = result[0]
            data = {members[i]: row[i + 1] for i in range(len(members))}
            return GuildXP(row[0], data)
        return None

    async def get_last(self, amount: int = 1) -> list[GuildXP]:
        result = await self._con.query(f'SELECT * FROM guild_xp ORDER BY time DESC LIMIT {amount}')
        members = await self.get_members()
        return [GuildXP(row[0], dict(zip(members, row[1:]))) for row in result]

    async def update_columns(self, names: list[str]) -> None:
        columns = await self.get_members()
        new_members = set(names).difference(columns)
        if new_members:
            add_string = ', '.join(f'ADD COLUMN "{name}" BIGINT' for name in new_members)
            await self._con.execute(f'ALTER TABLE guild_xp {add_string};')

    async def add(self, data: dict[str, int]) -> None:
        rounded_time = get_rounded_time(minutes=5)

        columns = ', '.join(f'"{key}"' for key in data)
        placeholders = ', '.join(f'${i + 2}' for i in range(len(data)))

        await self._con.execute(
            f'INSERT INTO guild_xp (time, {columns}) VALUES ($1, {placeholders}) ON CONFLICT(time)'
            ' DO NOTHING;',
            rounded_time,
            *data.values(),
        )

    async def cleanup(self) -> None:
        await self._con.execute(
            'DELETE FROM guild_xp WHERE time < (CURRENT_TIMESTAMP - \'7 DAY\'::interval) AND'
            ' to_char(time, \'MI\') != \'00\''
        )
        await self._con.execute(
            'DELETE FROM guild_xp WHERE time < (CURRENT_TIMESTAMP - \'14 DAY\'::interval) AND'
            ' to_char(time, \'HH24:MI\') != \'00:00\''
        )
