from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from logging import getLogger
from math import ceil, sqrt
from random import choices
from typing import TYPE_CHECKING

from discord import Embed, Webhook

from corkus.errors import CorkusException
from pianobot.utils import get_cycle

if TYPE_CHECKING:
    from pianobot import Pianobot


async def guild_awards(bot: Pianobot) -> None:
    dt = datetime.now(timezone.utc)
    if dt.day in {1, 15} and time(0, 0) <= dt.time() < time(0, 5):
        await update_for_cycle(bot, get_cycle(dt - timedelta(days=10)))
        results = await bot.database.guild_award_stats.get_for_cycle(get_cycle(dt - timedelta(days=10)))
        prev_results = await bot.database.guild_award_stats.get_for_cycle(get_cycle(dt - timedelta(days=20)))

        # prev_raids = {entry.username: entry.raid_count for entry in prev_results}
        # raid_res = [(entry.username, entry.raid_count - prev_raids.get(entry.username, 0)) for entry in results]
        prev_dt = dt - timedelta(days=10)
        start_date = datetime(prev_dt.year, prev_dt.month, 1 if prev_dt.day < 15 else 15, tzinfo=timezone.utc)
        raid_res = list((await bot.database.raid_log.get_between(start_date)).items())
        raid_res.sort(key=lambda x: x[1], reverse=True)

        prev_wars = {entry.username: entry.wars for entry in prev_results}
        war_res = [(entry.username, entry.wars - prev_wars.get(entry.username, 0)) for entry in results]
        war_res.sort(key=lambda x: x[1], reverse=True)

        prev_xp = {entry.username: entry.xp for entry in prev_results}
        xp_res = [
            (
                entry.username,
                entry.xp - prev_xp.get(entry.username, 0)
                if prev_xp.get(entry.username, 0) <= entry.xp
                else entry.xp
            )
            for entry in results
        ]
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
    prev_db_results = await bot.database.guild_award_stats.get_for_cycle(prev_cycle)
    prev_names = {entry.username for entry in prev_db_results}

    for member in guild_members:
        if member.username not in db_stats:
            raids = {}
            wars = 0
            try:
                player = await bot.corkus.player.getv3(member.uuid)
                raids = player.get('globalData', {}).get('raids', {}).get('list', {})
                wars = player.get('globalData', {}).get('wars', 0)
            except CorkusException as e:
                getLogger('tasks.guild_awards').warning(
                    'Error when fetching player data of `%s`: %s', member.username, e
                )
            await bot.database.guild_award_stats.add(member.username, cycle, raids, wars, member.contributed_xp)
            if prev_cycle and member.username not in prev_names:
                await bot.database.guild_award_stats.add(member.username, prev_cycle, raids, wars, member.contributed_xp)
        else:
            db_stat = db_stats[member.username]
            if member.is_online or member.contributed_xp != db_stat.xp:
                try:
                    player = await bot.corkus.player.getv3(member.uuid)
                    raids = player.get('globalData', {}).get('raids', {})
                    if raids.get('total', 0) != db_stat.raid_count:
                        await bot.database.guild_award_stats.update_raids(member.username, cycle, raids.get('list', {}))
                    wars = player.get('globalData', {}).get('wars', None)
                    if wars is not None and wars != db_stat.wars:
                        for _ in range(max(0, wars - db_stat.wars)):
                            await bot.database.war_log.add(member.uuid)
                        await bot.database.guild_award_stats.update_wars(member.username, cycle, wars)
                except CorkusException as e:
                    getLogger('tasks.guild_awards').warning(
                        'Error when fetching player data of `%s`: %s', member.username, e
                    )
                if member.contributed_xp != db_stat.xp:
                    if member.contributed_xp > db_stat.xp:
                        await bot.database.raid_members.add_xp(member.uuid, member.contributed_xp - db_stat.xp)
                    await bot.database.guild_award_stats.update_xp(member.username, cycle, member.contributed_xp)


def draw_raid_raffle_winners(entries: list[tuple[str, int]], n: int = 3) -> tuple[list[tuple[str, int]], int]:
    entries = [(name, ceil(sqrt(amount))) for name, amount in entries]
    total_tickets = sum(e[1] for e in entries)

    winners = []
    for _ in range(min(n, len(entries))):
        names, weights = zip(*entries)
        winner_name = choices(names, weights)[0]
        for i, (name, _) in enumerate(entries):
            if name == winner_name:
                winners.append(entries.pop(i))
                break

    return winners, total_tickets


async def send_results(bot: Pianobot, cycle: str, results: list[list[tuple[str, int]]]) -> None:
    embed = Embed(title=f'Final award results for promotion cycle  `{cycle}`')
    for title, code, result in zip(['Guild Raids', 'Wars', 'Guild XP'], ['gss', 'js', 'less'], results):
        code_block = f'```{code}\n'
        for i, data in enumerate(result[:9]):
            code_block += f'{i + 1}. {data[0]} (+{data[1]})\n'
        embed.add_field(name=title, value=code_block + '```', inline=False)

    raffle_results, total_tickets = draw_raid_raffle_winners(results[0])
    header = f"Total tickets: {total_tickets}"
    code_block = f'```md\n{header}\n{"-" * len(header)}'
    for i, name in enumerate(raffle_results[:3]):
        code_block += f'{i + 1}. {name}\n'
    embed.add_field(name='Raid Raffle', value=code_block + '```', inline=False)

    if bot.member_update_channel is not None:
        webhook = Webhook.from_url(bot.member_update_channel, session=bot.session)
        await webhook.send(embed=embed, username='Eden Awards', avatar_url='https://cdn.discordapp.com/avatars/861602324543307786/83f879567954aee29bc9fd534bc05b1f.webp')
