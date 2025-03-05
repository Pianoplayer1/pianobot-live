from pianobot.db import Connection


class GuildAwardStats:
    def __init__(self, username: str, cycle: str, raids: int, wars: int, xp: int) -> None:
        self._username = username
        self._cycle = cycle
        self._raids = raids
        self._wars = wars
        self._xp = xp

    @property
    def username(self) -> str:
        return self._username

    @property
    def cycle(self) -> str:
        return self._cycle

    @property
    def raids(self) -> int:
        return self._raids

    @property
    def wars(self) -> int:
        return self._wars

    @property
    def xp(self) -> int:
        return self._xp

    def __str__(self) -> str:
        return f'{self._username} - {self._cycle} - {self._raids} - {self._wars} - {self._xp}'

    def __repr__(self) -> str:
        return f'{self._username} - {self._cycle} - {self._raids} - {self._wars} - {self._xp}'


class GuildAwardStatsTable:
    def __init__(self, con: Connection) -> None:
        self._con = con

    async def add(self, username: str, cycle: str, raids: int, wars: int, xp: int) -> None:
        await self._con.execute(
            'INSERT INTO guild_award_stats VALUES ($1, $2, $3, $4, $5)', username, cycle, raids, wars, xp
        )

    async def get_for_cycle(self, cycle: str) -> list[GuildAwardStats]:
        result = await self._con.query('SELECT * FROM guild_award_stats WHERE cycle = $1', cycle)
        return [GuildAwardStats(*row) for row in result]

    async def update_raids(self, username: str, cycle: str, raids: int) -> None:
        await self._con.execute(
            'UPDATE guild_award_stats SET raids = $1 WHERE username = $2 AND cycle = $3', raids, username, cycle
        )

    async def update_wars(self, username: str, cycle: str, wars: int) -> None:
        await self._con.execute(
            'UPDATE guild_award_stats SET wars = $1 WHERE username = $2 AND cycle = $3', wars, username, cycle
        )

    async def update_xp(self, username: str, cycle: str, xp: int) -> None:
        await self._con.execute(
            'UPDATE guild_award_stats SET xp = $1 WHERE username = $2 AND cycle = $3', xp, username, cycle
        )
