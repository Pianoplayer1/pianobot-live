from discord import Interaction, Member, Object, app_commands

from pianobot import Pianobot
from pianobot.utils.guild_tomes import send_formatted_list


class Tome(app_commands.Group):
    def __init__(self, bot: Pianobot) -> None:
        super().__init__(description='Manage the pending guild tome list')
        self.bot = bot

    @app_commands.command(description='Use this command when giving out a tome in-game')
    async def grant(self, interaction: Interaction, member: Member) -> None:
        await self.bot.database.guild_tomes.grant(member.id)
        start_text = f"{member.display_name} has been removed from the tome queue.\nCurrently pending tomes:\n\n"
        await send_formatted_list(self.bot, self.bot.tome_log_channel, start_text)

    @app_commands.command(description='Remove a member from the tome queue')
    async def deny(self, interaction: Interaction, member: Member) -> None:
        await self.bot.database.guild_tomes.deny(member.id)
        start_text = f"{member.display_name} has been removed from the tome queue.\nCurrently pending tomes:\n\n"
        await send_formatted_list(self.bot, self.bot.tome_log_channel, start_text)


async def setup(bot: Pianobot) -> None:
    bot.tree.add_command(Tome(bot), guild=Object(713710628258185258))


class FakeCtx:
    def __init__(self, interaction: Interaction) -> None:
        self.send = interaction.response.send_message
