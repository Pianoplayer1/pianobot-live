from datetime import datetime
from uuid import UUID

from pianobot.db import Connection


class Player:
    def __init__(
        self, uuid: UUID, last_seen: datetime
    ) -> None:
        self._uuid = uuid
        self._last_seen = last_seen

    @property
    def uuid(self) -> UUID:
        return self._uuid

    @property
    def last_seen(self) -> datetime:
        return self._last_seen


class PlayerTable:
    def __init__(self, con: Connection) -> None:
        self._con = con

    async def get_selected(self, uuids: list[UUID]) -> list[Player]:
        result = await self._con.query('SELECT uuid, last_seen FROM players WHERE uuid = ANY($1)', uuids)
        return [Player(row[0], row[1]) for row in result]

    async def add(self, uuid: UUID, last_seen: datetime) -> None:
        await self._con.execute('INSERT INTO players (uuid, last_seen) VALUES ($1, $2)', uuid, last_seen)

    async def add_multiple(self, uuids: list[UUID]):
        placeholder = ','.join(f"('{uuid}')" for uuid in uuids)
        await self._con.execute(f'INSERT INTO players (uuid) VALUES {placeholder} ON CONFLICT DO NOTHING')

    async def update_last_seen(self, uuids: list[UUID]) -> None:
        await self._con.execute('UPDATE players SET last_seen = CURRENT_TIMESTAMP WHERE uuid = ANY($1)', uuids)
