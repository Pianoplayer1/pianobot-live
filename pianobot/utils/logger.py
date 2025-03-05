from __future__ import annotations

from logging import Handler
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from pianobot import Pianobot


class DiscordLogHandler(Handler):
    def __init__(self, bot: Pianobot, channel_id: int):
        super().__init__()
        self.bot = bot
        self.channel = bot.get_channel(channel_id)

    def emit(self, record: Any) -> None:
        log_entry = self.format(record)
        if log_entry.startswith("We are being rate limited"):
            return
        messages = [
            f"```{log_entry[i * 1990:(i + 1) * 1990]}```"
            for i in range(len(log_entry) // 1990 + 1)
        ]
        self.bot.loop.create_task(self.send(messages))

    async def send(self, messages: list[str]) -> None:
        for message in messages:
            try:
                await self.channel.send(message)
            except Exception:
                pass
