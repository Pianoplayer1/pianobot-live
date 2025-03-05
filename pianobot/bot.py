from logging import Logger, getLogger
from os import getenv, listdir

from aiohttp import ClientSession
from corkus import Corkus
from discord import Intents, Message, TextChannel
from discord.ext.commands import Bot, when_mentioned_or
from discord.ext.commands.errors import ExtensionFailed

from pianobot.db.db_manager import DBManager
from pianobot.tasks import TaskRunner
from pianobot.utils import DiscordLogHandler, get_prefix


class Pianobot(Bot):
    corkus: Corkus
    database: DBManager
    enable_tracking: bool
    logger: Logger
    session: ClientSession
    member_update_channel: str | None
    xp_tracking_channel: str | None

    def __init__(self) -> None:
        intents = Intents.default()
        intents.members = True
        intents.message_content = True

        async def _get_prefixes(bot: Bot, message: Message) -> list[str]:
            prefix = await get_prefix(self.database.servers, message.guild)
            return when_mentioned_or(prefix)(bot, message)

        super().__init__(
            case_insensitive=True,
            command_prefix=_get_prefixes,
            help_command=None,
            intents=intents,
        )

        self.logger = getLogger('bot')
        self.enable_tracking = False
        self.database = DBManager()

        with open('tracked_guilds.txt', 'r', encoding='UTF-8') as file:
            self.tracked_guilds: dict[str, str] = {
                name: tag for line in file for (name, tag) in [line.strip().split(':')]
            }

    async def setup_hook(self) -> None:
        self.corkus = Corkus()
        await self.corkus.start()
        await self.database.connect()
        await self.database.guild_activity.update_columns(list(self.tracked_guilds.keys()))
        await self.database.guild_activity.cleanup()
        await self.database.guild_xp.cleanup()
        self.session = ClientSession()

        for folder in ['commands', 'events']:
            for extension in [f[:-3] for f in listdir(f'pianobot/{folder}') if f.endswith('.py')]:
                try:
                    await self.load_extension(f'pianobot.{folder}.{extension}')
                except ExtensionFailed as exc:
                    self.logger.warning('Skipped %s.%s: %s', folder, extension, exc.__cause__)

    async def on_ready(self) -> None:
        self.member_update_channel = getenv('MEMBER_CHANNEL', '')
        # member_update_channel = self.get_channel(int(getenv('MEMBER_CHANNEL', 0)))
        # if isinstance(member_update_channel, TextChannel):
        #     self.member_update_channel = member_update_channel
        # elif getenv('MEMBER_CHANNEL') is not None:
        #     self.logger.warning('Member update channel %s not found', getenv('MEMBER_CHANNEL'))

        self.xp_tracking_channel = getenv('XP_CHANNEL', '')
        # xp_tracking_channel = self.get_channel(int(getenv('XP_CHANNEL', 0)))
        # if isinstance(xp_tracking_channel, TextChannel):
        #     self.xp_tracking_channel = xp_tracking_channel
        # elif getenv('XP_CHANNEL') is not None:
        #     self.logger.warning('XP tracking channel %s not found', getenv('XP_CHANNEL'))

        getLogger().addHandler(DiscordLogHandler(self, 1337524156530688100))

        self.logger.info('Booted up')

        await TaskRunner(self).start_tasks()

    async def close(self) -> None:
        if self.corkus is not None:
            await self.corkus.close()
        await self.database.disconnect()
        if self.session is not None:
            await self.session.close()
        self.logger.info('Exited')
        await super().close()
