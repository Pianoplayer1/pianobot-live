from datetime import datetime

from pianobot.db import Connection


class MemberActivityTable:
    def __init__(self, con: Connection) -> None:
        self._con = con

    async def get_weeks(self) -> list[str]:
        result = await self._con.query(
            'SELECT column_name FROM information_schema.columns WHERE table_name ='
            ' \'member_activity\''
        )
        return [] if len(result) <= 1 else [column[0] for column in result]

    async def get_one(self, username: str, week: str) -> int | None:
        result = await self._con.query(
            'SELECT * FROM member_activity WHERE username = $1', username
        )
        weeks = await self.get_weeks()
        return int(result[0][weeks.index(week) + 1]) if result else None

    async def get(self, week: str) -> dict[str, int]:
        results = await self._con.query('SELECT * FROM member_activity')
        pos = (await self.get_weeks()).index(week)
        return {row[0]: row[pos] for row in results}

    async def get_usernames(self) -> list[str]:
        return [row[0] for row in await self._con.query('SELECT username FROM member_activity')]

    async def add(self, names: list[str]) -> None:
        iso_date = datetime.utcnow().isocalendar()
        date = f'"{iso_date.year}-{iso_date.week}"'
        if date[1:-1] not in await self.get_weeks():
            await self._con.execute(
                f'ALTER TABLE member_activity ADD COLUMN {date} INTEGER NOT NULL DEFAULT 0'
            )
        for name in set(names).difference(await self.get_usernames()):
            await self._con.execute('INSERT INTO member_activity(username) VALUES ($1)', name)

        placeholders = ', '.join(f'${i + 1}' for i in range(len(names)))

        await self._con.execute(
            f'UPDATE member_activity SET {date} = {date} + 1 WHERE username IN ({placeholders});',
            *names,
        )
