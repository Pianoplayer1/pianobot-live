from uuid import UUID

from pianobot.db import Connection


class RaidTable:
    def __init__(self, con: Connection) -> None:
        self._con = con

    async def get_for_player(self, uuid: UUID) -> dict[str, int]:
        result = await self._con.query('SELECT raid, amount FROM raids WHERE uuid = $1', uuid)
        return {row[0]: row[1] for row in result}

    async def prev_for_player(self, uuid: UUID) -> dict[str, int]:
        result = await self._con.query(
            'SELECT raid, amount FROM prev_raids WHERE uuid = $1'
            ' AND timestamp >= NOW() - INTERVAL 10 MINUTE',
            uuid,
        )
        return {row[0]: row[1] for row in result}

    async def set(self, uuid: UUID, raid: str, amount: int) -> None:
        await self._con.execute(
            (
                'INSERT INTO raids VALUES ($1, $2, $3)'
                ' ON CONFLICT (uuid, raid) DO UPDATE SET amount = EXCLUDED.amount'
            ),
            uuid,
            raid,
            amount,
        )

    async def set_prev(self, uuid: UUID, raid: str, amount: int) -> None:
        await self._con.execute(
            (
                'INSERT INTO prev_raids VALUES ($1, $2, $3) ON CONFLICT (uuid, raid)'
                ' DO UPDATE SET amount = EXCLUDED.amount, timestamp = CURRENT_TIMESTAMP'
            ),
            uuid,
            raid,
            amount,
        )
