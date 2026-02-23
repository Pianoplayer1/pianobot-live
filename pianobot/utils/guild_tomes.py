from datetime import datetime, timedelta, timezone

import discord
from discord.abc import Messageable

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pianobot import Pianobot
from pianobot.utils.pages import paginator
from pianobot.utils.time import format_time_since


class GuildTomeView(discord.ui.View):
    def __init__(self, bot: "Pianobot") -> None:
        super().__init__(timeout=None)
        self.add_item(GuildTomeButton(bot))


class GuildTomeButton(discord.ui.Button[GuildTomeView]):
    def __init__(self, bot: "Pianobot") -> None:
        super().__init__(
            style=discord.ButtonStyle.green,
            label="Join queue",
            custom_id="guild-tome-button",
            emoji=bot.get_emoji(1344788047031566459)
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction) -> None:
        discord_id = interaction.user.id
        if await self.bot.database.guild_tomes.pending_number_for(discord_id) >= 3:
            await interaction.response.send_message(
                "You have already queued up to three tomes!",
                ephemeral=True,
            )
            return
        last_request = await self.bot.database.guild_tomes.last_requested_for(discord_id)
        if last_request and last_request + timedelta(days=7) > datetime.now(timezone.utc):
            await interaction.response.send_message(
                "You have last requested a tome less than a week ago!",
                ephemeral=True,
            )
            return

        await self.bot.database.guild_tomes.add_request(discord_id)
        await interaction.response.send_message(
            "Successfully queued up for a guild tome!",
            ephemeral=True,
        )
        if self.bot.tome_log_channel:
            start_text = f"{interaction.user.display_name} queued up for a guild tome.\nCurrently pending tomes:\n\n"
            await send_formatted_list(self.bot, self.bot.tome_log_channel, start_text)


async def send_formatted_list(bot: "Pianobot", ctx: Messageable, start_text: str) -> None:
    columns = {"Discord Name": 48, "Amount": 8, "Requested At": 20}
    await paginator(
        ctx,
        await format_pending_list(bot),
        columns,
        separator_rows=0,
        start_text=start_text,
    )


async def format_pending_list(bot: "Pianobot") -> list[list[str]]:
    pending_tomes = await bot.database.guild_tomes.get_pending()
    return [
        [
            str(bot.get_guild(713710628258185258).get_member(discord_id).display_name),
            str(count),
            format_time_since(first_request)[1] + " ago"
        ]
        for discord_id, (count, first_request) in pending_tomes.items()
    ]
