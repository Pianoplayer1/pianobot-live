from datetime import datetime

from pianobot.db import Connection


class GuildTomeTable:
    def __init__(self, con: Connection) -> None:
        self._con = con

    async def get_pending(self) -> dict[int, tuple[int, int, datetime]]:
        result = await self._con.query(
            'SELECT'
            '   discord_id,'
            '   COUNT(*) FILTER (WHERE granted_at IS NULL AND denied_at IS NULL) AS pending_count,'
            '   COUNT(*) FILTER (WHERE granted_at IS NOT NULL) AS total_received,'
            '   MIN(requested_at) as first_request'
            ' FROM guild_tomes GROUP BY discord_id'
            ' HAVING COUNT(*) FILTER (WHERE granted_at IS NULL AND denied_at IS NULL) > 0'
            ' ORDER BY first_request DESC'
        )
        return {row[0]: (row[1], row[2], row[3]) for row in result}

    async def stats_for(self, discord_id: int) -> tuple[int, int, datetime | None]:
        result = await self._con.query(
            'SELECT'
            '   COUNT(*) FILTER (WHERE granted_at IS NULL AND denied_at IS NULL) AS total_pending,'
            '   COUNT(*) FILTER (WHERE granted_at IS NOT NULL) AS total_granted_before,'
            '   MAX(requested_at) AS latest_request'
            ' FROM guild_tomes WHERE discord_id = $1',
            discord_id,
        )
        return (result[0][0], result[0][1], result[0][2]) if result else (0, 0, None)

    async def add_request(self, discord_id: int) -> None:
        await self._con.execute('INSERT INTO guild_tomes VALUES ($1)', discord_id)

    async def grant(self, discord_id: int) -> bool:
        status = await self._con.execute(
            'UPDATE guild_tomes'
            ' SET granted_at = CURRENT_TIMESTAMP'
            ' WHERE discord_id = $1 AND requested_at = ('
            '  SELECT requested_at FROM guild_tomes'
            '  WHERE discord_id = $1 AND granted_at IS NULL AND denied_at IS NULL'
            '  ORDER BY requested_at LIMIT 1'
            ' )',
            discord_id,
        )
        return status == "UPDATE 1"

    async def deny(self, discord_id: int) -> bool:
        status = await self._con.execute(
            'UPDATE guild_tomes'
            ' SET denied_at = CURRENT_TIMESTAMP'
            ' WHERE discord_id = $1 AND requested_at = ('
            '  SELECT requested_at FROM guild_tomes'
            '  WHERE discord_id = $1 AND granted_at IS NULL AND denied_at IS NULL'
            '  ORDER BY requested_at LIMIT 1'
            ' )',
            discord_id,
        )
        return status == "UPDATE 1"
