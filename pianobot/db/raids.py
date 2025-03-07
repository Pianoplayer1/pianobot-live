from uuid import UUID

from pianobot.db import Connection


class RaidTable:
    def __init__(self, con: Connection) -> None:
        self._con = con

    async def get_for_player(self, uuid: UUID) -> dict[str, int]:
        result = await self._con.query('SELECT raid, amount FROM raids WHERE uuid = $1', uuid)
        return {row[0]: row[1] for row in result}

    async def set(self, uuid: UUID, raid: str, amount: int) -> None:
        await self._con.execute(
            (
                'INSERT INTO raids VALUES ($1, $2, $3) ON CONFLICT DO UPDATE'
                ' SET amount = $3 WHERE uuid = $1 AND raid = $2'
            ),
            uuid,
            raid,
            amount,
        )
