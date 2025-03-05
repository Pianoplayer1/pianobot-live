from __future__ import annotations

from logging import Handler
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pianobot import Pianobot


class DiscordLogHandler(Handler):
    def __init__(self, bot: Pianobot, channel_id: int):
        super().__init__()
        self.bot = bot
        self.channel = bot.get_channel(channel_id)

    def emit(self, record) -> None:
        log_entry = self.format(record)
        for i in range(len(log_entry) // 1990 + 1):
            try:
                self.bot.loop.create_task(
                    self.channel.send(f"```{log_entry[i * 1990:(i + 1) * 1990]}```")
                )
            except Exception:
                pass
