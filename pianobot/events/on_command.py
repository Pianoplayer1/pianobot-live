from discord.ext.commands import Bot, Cog, Context

from pianobot import Pianobot


class OnCommand(Cog):
    def __init__(self, bot: Pianobot) -> None:
        self.bot = bot

    @Cog.listener()
    async def on_command(self, ctx: Context[Bot]) -> None:
        self.bot.logger.info(
            f'{ctx.channel if ctx.guild is None else ctx.guild.name} -'
            f' {ctx.author.name}: {ctx.message.content}'
        )


async def setup(bot: Pianobot) -> None:
    await bot.add_cog(OnCommand(bot))
