from discord import Interaction, app_commands

from pianobot import Pianobot
from pianobot.utils import paginator


class Territories(app_commands.Group):
    def __init__(self, bot: Pianobot) -> None:
        super().__init__(description='View or edit the list of territories this bot listens to')
        self.bot = bot

    @app_commands.command(description='View the list of territories this bot listens to')
    async def list(self, interaction: Interaction) -> None:
        db_terrs = await self.bot.database.territories.get_all()
        await paginator(
            FakeCtx(interaction),
            sorted([[terr.name, terr.guild] for terr in db_terrs], key=lambda i: i[0]),
            {
                'Territory': len(max([terr.name for terr in db_terrs], key=len)) + 8,
                'Guild': len(max([terr.name for terr in db_terrs], key=len)) + 8,
            },
            revert_option=False,
            page_rows=20,
            separator_rows=10,
            enum=True,
        )

    @app_commands.command(description='Edit territories of the territory list')
    @app_commands.describe(territories='Comma-separated list of Wynncraft territories')
    async def add(self, interaction: Interaction, territories: str) -> None:
        if not interaction.permissions.manage_guild:
            await interaction.response.send_message(
                'You don\'t have the required permissions to perform this action!'
            )
            return
        territory_list = territories.split(', ')
        if len(territory_list) == 0:
            await interaction.response.send_message(
                'You have to specify at least one territory to add!'
            )
            return
        wynn_terrs = await self.bot.corkus.territory.list_all()
        failed = []
        for territory in territory_list:
            found = next(
                (terr for terr in wynn_terrs if terr.name.lower() == territory.lower()), None
            )
            if found is None:
                failed.append(territory)
            else:
                await self.bot.database.territories.add(
                    found.name, None if found.guild is None else found.guild.name
                )
        message = ''
        if len(territory_list) - len(failed) > 0:
            message += (
                f'Successfully added {len(territory_list) - len(failed)}'
                f' territor{"ies" if len(territory_list) - len(failed) > 1 else "y"}'
                ' to the territory list!\n\n'
            )
        if len(failed) > 0:
            failed_string = '-`' + '`\n-`'.join(failed) + '`\n'
            message += f'Invalid territor{"ies" if len(failed) > 1 else "y"}:\n{failed_string}'
        await interaction.response.send_message(message)

    @app_commands.command(description='Remove territories from the territory list')
    @app_commands.describe(territories='Comma-separated list of Wynncraft territories')
    async def remove(self, interaction: Interaction, territories: str) -> None:
        if not interaction.permissions.manage_guild:
            await interaction.response.send_message(
                'You don\'t have the required permissions to perform this action!'
            )
            return
        territory_list = territories.split(', ')
        if len(territory_list) == 0:
            await interaction.response.send_message(
                'You have to specify at least one territory to remove!'
            )
            return
        db_terrs = await self.bot.database.territories.get_all()
        failed = []
        for territory in territory_list:
            found = next(
                (terr for terr in db_terrs if terr.name.lower() == territory.lower()), None
            )
            if found is None:
                failed.append(territory)
            else:
                await self.bot.database.territories.remove(found.name)
        message = ''
        if len(territory_list) - len(failed) > 0:
            message += (
                f'Successfully removed {len(territory_list) - len(failed)}'
                f' territor{"ies" if len(territory_list) - len(failed) > 1 else "y"}'
                ' from the territory list!\n\n'
            )
        if failed:
            failed_string = '-`' + '`\n-`'.join(failed) + '`\n'
            message += f'Invalid territor{"ies" if len(failed) > 1 else "y"}:\n{failed_string}'
        await interaction.response.send_message(message)


async def setup(bot: Pianobot) -> None:
    if bot.enable_tracking:
        bot.tree.add_command(Territories(bot))


class FakeCtx:
    def __init__(self, interaction: Interaction) -> None:
        self.send = interaction.response.send_message
