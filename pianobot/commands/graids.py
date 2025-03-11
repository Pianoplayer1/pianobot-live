from discord.ext.commands import Bot, Cog, Context, command

from pianobot import Pianobot
from pianobot.utils import paginator


class GuildRaids(Cog):
    def __init__(self, bot: Pianobot) -> None:
        self.bot = bot

    @command(
        brief='Returns the guild raids done by Eden members.',
        help=(
            'This command returns the guild raids done by Eden members.'
        ),
        name='graids',
    )
    async def graids(self, ctx: Context[Bot], *, args: str = '') -> None:
        if args.lower() in ('p', 'pending'):
            raids = await self.bot.database.raid_log.get_new()
            if raids:
                data = [
                    [raid, str(count)]
                    for raid, count in sorted(list(raids.items()), key=lambda x: x[1])
                ]
                columns = {'Username': 22, 'Amount': 8}
                await paginator(ctx, data, columns, page_rows=20, separator_rows=0, enum=False)
            else:
                await ctx.send('No new raids have been logged.')
        elif args.lower() in ('r', 'reset') and ctx.guild:
            if ctx.author.guild_permissions.administrator:
                await self.bot.database.raid_log.reset_new()
                await ctx.send('All raids have been reset.')
            else:
                await ctx.send('You do not have the required permissions to reset the raids.')
            return
        else:
            await ctx.send('Not implemented yet...')


async def setup(bot: Pianobot) -> None:
    await bot.add_cog(GuildRaids(bot))
