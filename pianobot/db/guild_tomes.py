from datetime import datetime

from pianobot.db import Connection


class GuildTomeTable:
    def __init__(self, con: Connection) -> None:
        self._con = con

    async def get_pending(self) -> dict[int, tuple[int, datetime]]:
        result = await self._con.query(
            'SELECT discord_id, COUNT(*), MIN(requested_at) as first_request FROM guild_tomes'
            ' WHERE granted_at IS NULL AND denied_at IS NULL'
            ' GROUP BY discord_id ORDER BY first_request'
        )
        return {row[0]: (row[1], row[2]) for row in result}

    async def pending_number_for(self, discord_id: int) -> int:
        result = await self._con.query(
            'SELECT COUNT(*) FROM guild_tomes'
            ' WHERE discord_id = $1 AND granted_at IS NOT NULL AND denied_at IS NOT NULL',
            discord_id,
        )
        return result[0][0] if result else 0

    async def last_requested_for(self, discord_id: int) -> datetime | None:
        result = await self._con.query(
            'SELECT requested_at FROM guild_tomes WHERE discord_id = $1'
            ' ORDER BY requested_at DESC LIMIT 1',
            discord_id,
        )
        return result[0][0] if result else None

    async def add_request(self, discord_id: int) -> None:
        await self._con.execute('INSERT INTO guild_tomes VALUES ($1)', discord_id)

    async def grant(self, discord_id: int) -> None:
        await self._con.execute(
            'UPDATE guild_tomes'
            ' SET granted_at = CURRENT_TIMESTAMP'
            ' WHERE discord_id = ('
            '  SELECT discord_id FROM guild_tomes'
            '  WHERE discord_id = $1 AND granted_at IS NULL AND denied_at IS NULL'
            '  ORDER BY requested_at LIMIT 1'
            ' )',
            discord_id,
        )

    async def deny(self, discord_id: int) -> None:
        await self._con.execute(
            'UPDATE guild_tomes'
            ' SET denied_at = CURRENT_TIMESTAMP'
            ' WHERE discord_id = ('
            '  SELECT discord_id FROM guild_tomes'
            '  WHERE discord_id = $1 AND granted_at IS NULL AND denied_at IS NULL'
            '  ORDER BY requested_at LIMIT 1'
            ' )',
            discord_id,
        )
