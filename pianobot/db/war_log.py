from logging import getLogger
from uuid import UUID

from asyncpg import NotNullViolationError
from datetime import datetime

from pianobot.db import Connection


class WarLogTable:
    def __init__(self, con: Connection) -> None:
        self._con = con

    async def add(self, uuid: UUID) -> None:
        try:
            await self._con.execute(
                'INSERT INTO war_log (uuid) VALUES ($1)',
                uuid,
            )
        except NotNullViolationError:
            getLogger('db.war_log').warning('Failed to add log entry for (%s)', uuid)

    async def get_between(self, start: datetime | None = None, end: datetime | None = None) -> dict[str, int]:
        result = await self._con.query(
            'SELECT m.name, count(*) FROM members m, war_log l'
            ' WHERE m.uuid = l.uuid AND l.timestamp >= $1 AND l.timestamp < $2'
            ' GROUP BY m.name',
            start or datetime.min,
            end or datetime.max,
        )
        return {row[0]: row[1] for row in result}
