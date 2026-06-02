"""Typed Pydantic models for the Wynncraft v3 API responses."""

from datetime import datetime
from uuid import UUID

from pydantic import (
    AliasPath,
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    model_validator,
)

GUILD_RANKS = ("recruit", "recruiter", "captain", "strategist", "chief", "owner")


class GuildMember(BaseModel):
    """One guild member as returned by `/v3/guild/{query}`."""

    model_config = ConfigDict(populate_by_name=True)

    uuid: UUID
    username: str
    rank: str
    joined_at: datetime = Field(alias="joined")
    last_join_at: datetime | None = Field(default=None, alias="lastJoin")
    online: bool = False
    server: str | None = None
    contributed_xp: int = Field(default=0, alias="contributed")
    wars: int = Field(default=0, validation_alias=AliasPath("globalData", "wars"))
    raid_counts: dict[str, int] = Field(
        default_factory=dict,
        validation_alias=AliasPath("globalData", "currentGuildRaids", "list"),
    )
    total_level: int | None = Field(
        default=None, validation_alias=AliasPath("globalData", "totalLevel")
    )
    completed_quests: int | None = Field(
        default=None, validation_alias=AliasPath("globalData", "completedQuests")
    )
    total_dungeons: int | None = Field(
        default=None, validation_alias=AliasPath("globalData", "dungeons", "total")
    )
    total_raids: int | None = Field(
        default=None, validation_alias=AliasPath("globalData", "raids", "total")
    )
    playtime: float | None = Field(
        default=None, validation_alias=AliasPath("globalData", "playtime")
    )
    content_completion: int | None = Field(
        default=None, validation_alias=AliasPath("globalData", "contentCompletion")
    )
    mobs_killed: int | None = Field(
        default=None, validation_alias=AliasPath("globalData", "mobsKilled")
    )
    chests_found: int | None = Field(
        default=None, validation_alias=AliasPath("globalData", "chestsFound")
    )
    world_events: int | None = Field(
        default=None, validation_alias=AliasPath("globalData", "worldEvents")
    )
    lootruns: int | None = Field(
        default=None, validation_alias=AliasPath("globalData", "lootruns")
    )
    caves: int | None = Field(
        default=None, validation_alias=AliasPath("globalData", "caves")
    )
    pvp_kills: int | None = Field(
        default=None, validation_alias=AliasPath("globalData", "pvp", "kills")
    )
    pvp_deaths: int | None = Field(
        default=None, validation_alias=AliasPath("globalData", "pvp", "deaths")
    )
    weekly_completed: bool | None = Field(
        default=None, validation_alias=AliasPath("weekly", "completed")
    )
    weekly_streak: int | None = Field(
        default=None, validation_alias=AliasPath("weekly", "streak")
    )


class Guild(BaseModel):
    """Full guild response with flattened member list across all ranks."""

    model_config = ConfigDict(populate_by_name=True)

    uuid: UUID
    name: str
    prefix: str
    level: int = 0
    xp_percent: int = Field(default=0, alias="xpPercent")
    territories: int = 0
    wars: int | None = Field(default=0)
    total_raids: int = Field(default=0, alias="raids")
    created_at: datetime = Field(alias="created")
    members: list[GuildMember] = Field(default_factory=list)
    member_total: int = 0
    online_total: int = Field(default=0, alias="online")

    @model_validator(mode="before")
    @classmethod
    def _flatten_members(cls, data: object) -> object:
        """Promote nested members.{rank}.{username}.* into a flat list."""
        if not isinstance(data, dict):
            return data
        members_obj = data.get("members")
        if not isinstance(members_obj, dict):
            return data
        total = members_obj.get("total", 0)
        flat: list[dict[str, object]] = []
        for rank_key in GUILD_RANKS:
            rank_block = members_obj.get(rank_key)
            if not isinstance(rank_block, dict):
                continue
            for username, member_data in rank_block.items():
                if isinstance(member_data, dict):
                    flat.append(
                        {
                            **member_data,
                            "username": username,
                            "rank": rank_key.capitalize(),
                        }
                    )
        return {**data, "members": flat, "member_total": total}


class OnlinePlayers(BaseModel):
    """Aggregate online-players response (`/v3/player`), keyed by username."""

    total: int = 0
    players: dict[str, str | None] = Field(default_factory=dict)


class OnlinePlayersByUuid(BaseModel):
    """Online-players response (`/v3/player?identifier=uuid`), keyed by UUID."""

    total: int = 0
    players: dict[UUID, str | None] = Field(default_factory=dict)


class Player(BaseModel):
    """A player's main stats as returned by `/v3/player/{query}`."""

    model_config = ConfigDict(populate_by_name=True)

    username: str
    online: bool
    server: str | None
    uuid: UUID
    rank: str
    support_rank: str | None = Field(alias="supportRank")
    last_online: datetime | None = Field(alias="lastJoin")
    joined: datetime | None = Field(default=None, alias="firstJoin")
    playtime: float = 0.0
    total_level: int = Field(
        default=0, validation_alias=AliasPath("globalData", "totalLevel")
    )
    completed_quests: int = Field(
        default=0, validation_alias=AliasPath("globalData", "completedQuests")
    )
    total_raids: int = Field(
        default=0, validation_alias=AliasPath("globalData", "raids", "total")
    )
    total_dungeons: int = Field(
        default=0, validation_alias=AliasPath("globalData", "dungeons", "total")
    )


class GuildLeaderboardEntry(BaseModel):
    """One row from `/v3/leaderboards/{type}`."""

    model_config = ConfigDict(populate_by_name=True)

    uuid: UUID | None = None
    name: str = ""
    prefix: str = ""
    restricted: bool = False

    xp: int | None = None
    territories: int | None = None
    wars: int | None = None
    level: int | None = None
    members: int | None = None
    total_raids: int | None = Field(default=None, alias="totalRaids")

    @property
    def score(self) -> int:
        """Primary ranking value for this leaderboard row."""
        for v in (
            self.total_raids,
            self.xp,
            self.wars,
            self.territories,
            self.level,
            self.members,
        ):
            if v is not None:
                return v
        return 0


class TerritorySnapshot(BaseModel):
    """One map territory with its current owning guild (if any)."""

    model_config = ConfigDict(populate_by_name=True)

    name: str
    guild_uuid: UUID | None = Field(
        default=None, validation_alias=AliasPath("guild", "uuid")
    )
    guild_name: str | None = Field(
        default=None, validation_alias=AliasPath("guild", "name")
    )
    acquired_at: datetime = Field(alias="acquired")


class TerritoryList(RootModel[list[TerritorySnapshot]]):
    """Wrapper that promotes `/guild/list/territory`'s name-keyed dict to a list."""

    @model_validator(mode="before")
    @classmethod
    def _flatten(cls, data: object) -> object:
        if isinstance(data, dict):
            return [{**v, "name": k} for k, v in data.items() if isinstance(v, dict)]
        return data


class GuildLeaderboardResponse(RootModel[list[GuildLeaderboardEntry]]):
    """Wrapper that strips the ranking-position keys from the response dict."""

    @model_validator(mode="before")
    @classmethod
    def _flatten(cls, data: object) -> object:
        if isinstance(data, dict):
            return list(data.values())
        raise ValueError(f"Unexpected leaderboard shape: {type(data).__name__}")


class GuildListEntry(BaseModel):
    """One entry from ``GET /v3/guild/list/guild`` (name-keyed response)."""

    uuid: UUID
    prefix: str


class GuildListResponse(RootModel[dict[str, GuildListEntry]]):
    """Full guild-list response: maps guild name to uuid + prefix."""

    def to_uuid_map(self) -> dict[UUID, tuple[str, str]]:
        """Return ``{uuid: (name, prefix)}`` for all entries."""
        return {entry.uuid: (name, entry.prefix) for name, entry in self.root.items()}
