from __future__ import annotations
from datetime import datetime
from typing import Union

from iso8601 import iso8601

from .base import CorkusBase
from .partial_guild import PartialGuild
from .territory_location import TerritoryLocation

class Territory(CorkusBase):
    """Territories are areas which may be claimed by a :py:class:`Guild` to receive benefits."""

    def __init__(self, corkus: Corkus, attributes: dict, name: str):
        super().__init__(corkus, attributes)
        self._name = name

    @property
    def name(self) -> str:
        """The name of the territory."""
        return self._name

    @property
    def guild(self) -> Union[PartialGuild, None]:
        """Guild that currently holds the territory."""
        guild = self._attributes.get("guild", None)
        if guild is None or guild.get("name", "") == "Nobody":
            return None
        else:
            return PartialGuild(self._corkus, guild.get("name", ""))

    @property
    def acquired(self) -> datetime:
        """Datetime when the territory was acquired."""
        return iso8601.parse_date(self._attributes.get("acquired", "1970"))

    @property
    def location(self) -> TerritoryLocation:
        """The location of this territory."""
        return TerritoryLocation(self._corkus, self._attributes.get("location", {}))

    def __repr__(self) -> str:
        return f"<Territory name={self.name!r} guild={self.guild}>"
