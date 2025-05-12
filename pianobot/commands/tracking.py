from discord import Embed, Interaction, Role, TextChannel, app_commands

from pianobot import Pianobot

RANKS = ['Recruit', 'Recruiter', 'Captain', 'Strategist', 'Chief', 'Owner']


class Tracking(app_commands.Group):
    def __init__(self, bot: Pianobot) -> None:
        super().__init__(
            description='View or configure territory tracking options for this server',
            guild_only=True,
        )
        self.bot = bot

    @app_commands.command(description='Overview of current territory tracking options')
    async def overview(self, interaction: Interaction) -> None:
        if interaction.guild is None or interaction.guild_id is None:
            await interaction.response.send_message('This command can only be used in a server.')
            return
        current_server = await self.bot.database.servers.get(interaction.guild_id)
        assert current_server is not None
        channel = (
            interaction.guild.get_channel(current_server.territory_log_channel)
            if current_server.territory_log_channel is not None
            else None
        )
        role = (
            interaction.guild.get_role(current_server.ping_role)
            if current_server.ping_role is not None
            else None
        )
        role_msg = 'does not ping a role' if role is None else f'pings {role.mention}'

        embed = Embed(
            description=(
                f'Not active at the moment. Use `/tracking channel`'
                ' to start territory tracking!'
            )
            if channel is None
            else (
                f'Currently running in {channel.mention}, {role_msg} if a territory gets taken.'
            ),
            color=0xFFFF00 if channel is None else 0x00FF00,
        )
        embed.set_author(
            name='Eden Territory Tracking',
            icon_url=(
                'https://cdn.discordapp.com/attachments/'
                '784114583974445077/802578487252090950/eden100.png'
            ),
        )
        embed.add_field(
            inline=False,
            name=(
                'Pings disabled'
                if current_server.ping_interval is None
                else f'Ping cooldown: {current_server.ping_interval} minutes'
            ),
            value=f'*Configure with* `/tracking ping <minutes>`*.*',
        )
        embed.add_field(
            inline=False,
            name=(
                'Pings regardless of online members'
                if current_server.ping_rank is None
                else f'Pings unless a {RANKS[current_server.ping_rank]} is online'
            ),
            value=(
                f'*Configure with* `/tracking rank <stars>`*, '
                'use -1 as value to ping regardless of online members.*'
            ),
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        description='Set this channel for tracking messages, use command again to disable tracking'
    )
    async def channel(self, interaction: Interaction) -> None:
        if interaction.guild_id is None or not isinstance(interaction.channel, TextChannel):
            await interaction.response.send_message('This command can only be used in a server.')
            return
        current_server = await self.bot.database.servers.get(interaction.guild_id)
        assert current_server is not None
        if not interaction.permissions.manage_channels:
            await interaction.response.send_message(
                'You don\'t have the required permissions to perform this action!'
            )
            return
        if current_server.territory_log_channel == interaction.channel_id:
            await self.bot.database.servers.update_territory_log_channel(
                interaction.guild_id, None
            )
            await interaction.response.send_message('Territory tracking toggled off.')
        else:
            await self.bot.database.servers.update_territory_log_channel(
                interaction.guild_id, interaction.channel_id
            )
            await interaction.response.send_message(
                f'Territory tracking will be sent in {interaction.channel.mention}.'
            )

    @app_commands.command(description='View or configure the territory tracking ping interval')
    @app_commands.describe(interval='The new ping interval in minutes, 0 to turn pings off')
    async def ping(self, interaction: Interaction, interval: int | None = None) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message('This command can only be used in a server.')
            return
        current_server = await self.bot.database.servers.get(interaction.guild_id)
        assert current_server is not None
        if interval is None:
            text = (
                'is currently disabled.'
                if current_server.ping_interval is None
                else f'cooldown: `{current_server.ping_interval} minutes`'
            )
            await interaction.response.send_message(f'Territory ping {text}')
            return
        if not interaction.permissions.manage_channels:
            await interaction.response.send_message(
                'You don\'t have the required permissions to perform this action!'
            )
            return
        if interval == 0:
            interval = None
        await self.bot.database.servers.update_ping_interval(interaction.guild_id, interval)
        await interaction.response.send_message(
            'Territory ping toggled off.'
            if interval is None
            else f'Territory ping cooldown changed to {interval} minutes.'
        )

    @app_commands.command(description='View or configure the role this bot will ping')
    @app_commands.describe(role='The role that will get pinged')
    async def role(self, interaction: Interaction, role: Role | None = None) -> None:
        if interaction.guild is None or interaction.guild_id is None:
            await interaction.response.send_message('This command can only be used in a server.')
            return
        current_server = await self.bot.database.servers.get(interaction.guild_id)
        assert current_server is not None
        if role is None:
            if current_server.ping_role is None:
                await interaction.response.send_message('No territory ping role configured')
            else:
                guild_role = interaction.guild.get_role(current_server.ping_role)
                current_role = '*invalid*' if guild_role is None else f'`{guild_role.name}`'
                await interaction.response.send_message(f'Territory ping role: {current_role}')
            return
        if not interaction.permissions.manage_channels:
            await interaction.response.send_message(
                'You don\'t have the required permissions to perform this action!'
            )
            return
        await self.bot.database.servers.update_ping_role(interaction.guild_id, role.id)
        await interaction.response.send_message(f'Territory ping role changed to `{role.name}`.')

    @app_commands.command(description='Configure when pings will happen or view current setting')
    @app_commands.choices(
        rank=[
            app_commands.Choice(name='Always ping', value=-1),
            app_commands.Choice(name='Recruit', value=0),
            app_commands.Choice(name='Recruiter', value=1),
            app_commands.Choice(name='Captain', value=2),
            app_commands.Choice(name='Strategist', value=3),
            app_commands.Choice(name='Chief', value=4),
            app_commands.Choice(name='Owner', value=5),
        ],
    )
    @app_commands.describe(rank='Bot will ping unless one of the chosen rank or higher is online')
    async def rank(self, interaction: Interaction, rank: int | None = None) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message('This command can only be used in a server.')
            return
        current_server = await self.bot.database.servers.get(interaction.guild_id)
        if current_server is None:
            await interaction.response.send_message(
                'An internal error occurred, please try again later.'
            )
            return
        if rank is None:
            if current_server.ping_rank is None:
                await interaction.response.send_message(
                    'Pings are always on, regardless of online members.'
                )
            else:
                await interaction.response.send_message(
                    f'Pings are disabled when at least one {RANKS[current_server.ping_rank]} is'
                    ' online.'
                )
            return
        if not interaction.permissions.manage_channels:
            await interaction.response.send_message(
                'You don\'t have the required permissions to perform this action!'
            )
            return
        if rank == -1:
            await self.bot.database.servers.update_ping_rank(interaction.guild_id, None)
            await interaction.response.send_message('Ping are now always active.')
        else:
            await self.bot.database.servers.update_ping_rank(interaction.guild_id, rank)
            await interaction.response.send_message(
                f'Pings will be deactivated when at least one {RANKS[rank]} is online.'
            )


async def setup(bot: Pianobot) -> None:
    if bot.enable_tracking:
        bot.tree.add_command(Tracking(bot))
