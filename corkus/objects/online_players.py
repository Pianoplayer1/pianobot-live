from __future__ import annotations
from typing import List

from .base import CorkusBase
from .uuid import CorkusUUID
from .server import Server
from .partial_online_player import PartialOnlinePlayer

class OnlinePlayers(CorkusBase):
    """List all running servers and players that are online on them."""
    @property
    def servers(self) -> List[Server]:
        """List all running servers."""
        return [Server(self._corkus, s, [p for p, ps in self._attributes.items() if ps == s]) for s in set(self._attributes.values())]

    @property
    def players(self) -> List[PartialOnlinePlayer]:
        """List all online players."""
        return [PartialOnlinePlayer(self._corkus, self, username = p) for p in self._attributes]

    @property
    def uuid_players(self) -> List[PartialOnlinePlayer]:
        return [PartialOnlinePlayer(self._corkus, self, uuid=CorkusUUID(p)) for p in self._attributes]

    def __repr__(self) -> str:
        return f"<OnlinePlayers servers={len(self.servers)} players={len(self.players)}>"
