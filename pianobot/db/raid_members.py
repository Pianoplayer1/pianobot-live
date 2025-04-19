from uuid import UUID

from pianobot.db import Connection


class RaidMemberTable:
    def __init__(self, con: Connection) -> None:
        self._con = con

    async def get_all(self) -> dict[UUID, int]:
        result = await self._con.query('SELECT uuid, xp FROM raid_members')
        return {row[0]: row[1] for row in result}

    async def add(self, uuid: UUID, xp: int) -> None:
        await self._con.execute('INSERT INTO raid_members (uuid, xp) VALUES ($1, $2)', uuid, xp)

    async def add_raid(self, uuid: UUID) -> None:
        with open('emeralds.txt', 'r', encoding='UTF-8') as f:
            emeralds_per_raid = int(f.readline())
        await self._con.execute(
            (
                'UPDATE raid_members SET pending_raids = pending_raids + $1,'
                ' pending_aspects = pending_aspects + 1 where uuid = $2'
            ),
            emeralds_per_raid,
            uuid
        )

    async def get_pending(self) -> dict[str, int]:
        result = await self._con.query(
            'SELECT name, pending_raids FROM members m, raid_members r'
            ' where m.uuid = r.uuid and pending_raids > 0',
        )
        return {row[0]: row[1] for row in result}

    async def reset_pending(self, username: str) -> None:
        await self._con.execute(
            'UPDATE raid_members SET pending_raids = MOD(pending_raids, 4096)'
            ' WHERE uuid = (SELECT uuid FROM members WHERE name = $1)',
            username
        )
    
    async def get_aspects(self) -> dict[str, int]:
        result = await self._con.query(
            'SELECT name, pending_aspects FROM members m, raid_members r'
            ' where m.uuid = r.uuid and pending_aspects > 0',
        )
        return {row[0]: row[1] for row in result}

    async def reset_aspects(self, username: str | None) -> None:
        if username is not None:
            await self._con.execute(
                'UPDATE raid_members SET pending_aspects = MOD(pending_aspects, 2)'
                ' WHERE uuid = (SELECT uuid FROM members WHERE name = $1)',
                username
            )
        else:
            await self._con.execute(
                'UPDATE raid_members SET pending_aspects = MOD(pending_aspects, 2)'
            )

    async def remove(self, uuid: UUID) -> None:
        await self._con.execute('DELETE FROM raid_members WHERE uuid = $1', uuid)

    async def update_xp(self, uuid: UUID, xp: int) -> None:
        await self._con.execute('UPDATE raid_members SET xp = $1 WHERE uuid = $2', xp, uuid)
