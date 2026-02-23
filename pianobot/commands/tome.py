from discord import Interaction, Member, Object, app_commands

from pianobot import Pianobot


class Tome(app_commands.Group):
    def __init__(self, bot: Pianobot) -> None:
        super().__init__(description='Manage the pending guild tome list')
        self.bot = bot

    @app_commands.command(description='Use this command when giving out a tome in-game')
    async def grant(self, interaction: Interaction, member: Member) -> None:
        await self.bot.database.guild_tomes.grant(member.id)

    @app_commands.command(description='Remove a member from the tome queue')
    async def deny(self, interaction: Interaction, member: Member) -> None:
        await self.bot.database.guild_tomes.deny(member.id)


async def setup(bot: Pianobot) -> None:
    bot.tree.add_command(Tome(bot), guild=Object(682671629213368351))


class FakeCtx:
    def __init__(self, interaction: Interaction) -> None:
        self.send = interaction.response.send_message
