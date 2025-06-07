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

    async def add_raid(self, username: str) -> None:
        with open('emeralds.txt', 'r', encoding='UTF-8') as f:
            emeralds_per_raid = int(f.readline())
        await self._con.execute(
            (
                'UPDATE raid_members SET pending_raids = pending_raids + $1,'
                ' pending_aspects = CASE WHEN pending_aspects < 0 THEN -1 ELSE pending_aspects + 1 END'
                ' where uuid = (SELECT uuid FROM members WHERE name = $2)'
            ),
            emeralds_per_raid,
            username
        )

    async def add_xp(self, uuid: UUID, amount: int) -> None:
        old_amount = (await self._con.query(
            'SELECT pending_xp FROM raid_members WHERE uuid = $1',
            uuid,
        ))[0][0]
        rewards = (old_amount + amount) // 1000000000 > old_amount // 1000000000
        if rewards:
            with open('xp_emeralds.txt', 'r', encoding='UTF-8') as f:
                rewards *= int(f.readline())
        await self._con.execute(
            'UPDATE raid_members SET pending_xp = pending_xp + $1, xp_ems = xp_ems + $2 where uuid = $3',
            amount,
            rewards,
            uuid,
        )

    async def get_xp(self) -> dict[str, (int, int)]:
        result = await self._con.query(
            'SELECT name, pending_xp, xp_ems FROM members m, raid_members r'
            ' where m.uuid = r.uuid and xp_ems > 0',
        )
        return {row[0]: (row[1], row[2]) for row in result}

    async def reset_xp(self, username: str) -> bool:
        result = await self._con.execute(
            'UPDATE raid_members SET pending_xp = MOD(pending_xp, 1000000000), xp_ems = MOD(xp_ems, 4096)'
            ' WHERE uuid = (SELECT uuid FROM members WHERE name ILIKE $1)',
            username
        )
        return result.endswith('1')

    async def set_aspects(self, username: str, amount: int) -> bool:
        result = await self._con.execute(
            'UPDATE raid_members SET pending_aspects = $1'
            ' where uuid = (SELECT uuid FROM members WHERE name ILIKE $2)',
            amount,
            username
        )
        return result.endswith('1')

    async def get_blocked_aspects(self) -> list[str]:
        result = await self._con.query(
            'SELECT name FROM members m, raid_members r'
            ' where m.uuid = r.uuid and pending_aspects < 0',
        )
        return [row[0] for row in result]

    async def get_pending(self) -> dict[str, int]:
        result = await self._con.query(
            'SELECT name, pending_raids FROM members m, raid_members r'
            ' where m.uuid = r.uuid and pending_raids > 0',
        )
        return {row[0]: row[1] for row in result}

    async def get_pending_left(self) -> dict[UUID, int]:
        result = await self._con.query(
            'SELECT uuid, pending_raids FROM raid_members where pending_raids > 0',
        )
        return {row[0]: row[1] for row in result}

    async def reset_pending(self, username: str) -> bool:
        result = await self._con.execute(
            'UPDATE raid_members SET pending_raids = MOD(pending_raids, 4096)'
            ' WHERE uuid = (SELECT uuid FROM members WHERE name ILIKE $1) OR uuid = $1',
            username
        )
        return result.endswith('1')

    async def get_aspects(self) -> dict[str, int]:
        result = await self._con.query(
            'SELECT name, pending_aspects FROM members m, raid_members r'
            ' where m.uuid = r.uuid and pending_aspects > 0',
        )
        return {row[0]: row[1] for row in result}

    async def get_aspects_left(self) -> dict[UUID, int]:
        result = await self._con.query(
            'SELECT uuid, pending_aspects FROM raid_members where pending_aspects > 0',
        )
        return {row[0]: row[1] for row in result}

    async def reset_aspects(self, username: str | None = None) -> bool:
        if username is not None:
            result = await self._con.execute(
                'UPDATE raid_members SET pending_aspects = MOD(pending_aspects, 2)'
                ' WHERE uuid = (SELECT uuid FROM members WHERE name ILIKE $1) OR uuid = $1',
                username
            )
            return result.endswith('1')
        await self._con.execute(
            'UPDATE raid_members SET pending_aspects = MOD(pending_aspects, 2)'
        )
        return True

    async def remove(self, uuid: UUID) -> None:
        await self._con.execute('DELETE FROM raid_members WHERE uuid = $1', uuid)

    async def update_xp(self, uuid: UUID, xp: int) -> None:
        await self._con.execute('UPDATE raid_members SET xp = $1 WHERE uuid = $2', xp, uuid)
