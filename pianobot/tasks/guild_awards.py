from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from corkus.errors import CorkusException
from discord import Embed, Webhook
from datetime import datetime, time, timedelta, timezone

from pianobot.utils import get_cycle

if TYPE_CHECKING:
    from pianobot import Pianobot


async def guild_awards(bot: Pianobot) -> None:
    dt = datetime.now(timezone.utc)
    if (dt.day == 1 or dt.day == 15) and time(0, 0) <= dt.time() < time(0, 5):
        await update_for_cycle(bot, get_cycle(dt - timedelta(days=10)))
        results = await bot.database.guild_award_stats.get_for_cycle(get_cycle(dt - timedelta(days=10)))
        prev_results = await bot.database.guild_award_stats.get_for_cycle(get_cycle(dt - timedelta(days=20)))

        prev_raids = {entry.username: entry.raids for entry in prev_results}
        raid_res = [(entry.username, entry.raids - prev_raids.get(entry.username, 0)) for entry in results]
        raid_res.sort(key=lambda x: x[1], reverse=True)

        prev_wars = {entry.username: entry.wars for entry in prev_results}
        war_res = [(entry.username, entry.wars - prev_wars.get(entry.username, 0)) for entry in results]
        war_res.sort(key=lambda x: x[1], reverse=True)

        prev_xp = {entry.username: entry.xp for entry in prev_results}
        xp_res = [(entry.username, entry.xp - prev_xp.get(entry.username, 0)) for entry in results]
        xp_res.sort(key=lambda x: x[1], reverse=True)

        await send_results(bot, get_cycle(dt - timedelta(days=10)), [raid_res, war_res, xp_res])

    await update_for_cycle(bot, get_cycle(dt), get_cycle(dt - timedelta(days=20 if 8 < dt.day < 15 or 22 < dt.day else 10)))


async def update_for_cycle(bot: Pianobot, cycle: str, prev_cycle: str | None = None) -> None:
    try:
        guild = await bot.corkus.guild.get('Eden')
        guild_members = guild.members
    except CorkusException as e:
        getLogger('tasks.guild_awards').warning('Error when fetching guild data of `Eden`: %s', e)
        return

    db_result = await bot.database.guild_award_stats.get_for_cycle(cycle)
    db_stats = {entry.username: entry for entry in db_result}
    xp_per_raid = 100 / 3 * (1.15 ** guild.level - 1)

    for member in guild_members:
        if member.username not in db_stats:
            raids = 0
            wars = 0
            try:
                player = await bot.corkus.player.getv3(member.uuid)
                raids = player.get('globalData', {}).get('raids', {}).get('total', 0)
                wars = player.get('globalData', {}).get('wars', 0)
            except CorkusException as e:
                getLogger('tasks.guild_awards').warning(
                    'Error when fetching player data of `%s`: %s', member.username, e
                )
            await bot.database.guild_award_stats.add(member.username, cycle, raids, wars, member.contributed_xp)
            if prev_cycle:
                await bot.database.guild_award_stats.add(member.username, prev_cycle, raids, wars, member.contributed_xp)
        else:
            db_stat = db_stats[member.username]
            if member.is_online or member.contributed_xp != db_stat.xp:
                try:
                    player = await bot.corkus.player.getv3(member.uuid)
                    raids = player.get('globalData', {}).get('raids', {}).get('total', None)
                    if raids is not None and raids != db_stat.raids:
                        if member.contributed_xp - db_stat.xp >= xp_per_raid:
                            getLogger('tasks.guild_awards').info(
                                'Possible guild raid: %s with %d xp',
                                member.username,
                                member.contributed_xp - db_stat.xp,
                            )
                        await bot.database.guild_award_stats.update_raids(member.username, cycle, raids)
                    wars = player.get('globalData', {}).get('wars', None)
                    if wars is not None and wars != db_stat.wars:
                        await bot.database.guild_award_stats.update_wars(member.username, cycle, wars)
                except CorkusException as e:
                    getLogger('tasks.guild_awards').warning(
                        'Error when fetching player data of `%s`: %s', member.username, e
                    )
                if member.contributed_xp != db_stat.xp:
                    await bot.database.guild_award_stats.update_xp(member.username, cycle, member.contributed_xp)

async def send_results(bot: Pianobot, cycle: str, results: list[list[tuple[str, int]]]) -> None:
    embed = Embed(title=f'Final award results for promotion cycle  `{cycle}`')
    for title, code, result in zip(['Raids', 'Wars', 'Guild XP'], ['gss', 'js', 'less'], results):
        code_block = f'```{code}\n'
        for i, data in enumerate(result[:3]):
            code_block += f'{i}. {data[0]} (+{data[1]})\n'
        embed.add_field(name=title, value=code_block + '```')
    if bot.member_update_channel is not None:
        webhook = Webhook.from_url(bot.member_update_channel, session=bot.session)
        await webhook.send(embed=embed, username='Eden Awards', avatar_url='https://cdn.discordapp.com/avatars/861602324543307786/83f879567954aee29bc9fd534bc05b1f.webp')
