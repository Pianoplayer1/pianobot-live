from logging import getLogger
from uuid import UUID

from asyncpg import NotNullViolationError

from pianobot.db import Connection


class RaidLogTable:
    def __init__(self, con: Connection) -> None:
        self._con = con

    async def add(self, uuid: UUID, name: str) -> None:
        try:
            await self._con.execute(
                'INSERT INTO raid_log (uuid, raid_id)'
                ' VALUES ($1, (SELECT id FROM raid_names WHERE name = $2))',
                uuid,
                name
            )
        except NotNullViolationError:
            getLogger('db.raid_log').warning('Failed to add log entry for (%s, %s)', uuid, name)
