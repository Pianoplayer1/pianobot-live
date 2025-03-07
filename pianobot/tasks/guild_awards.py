from __future__ import annotations

from logging import getLogger
from math import ceil
from typing import TYPE_CHECKING

from corkus.errors import CorkusException
from discord import Embed, File, Webhook
from datetime import datetime, time, timedelta, timezone

from pianobot.utils import display_short, get_cycle

if TYPE_CHECKING:
    from pianobot import Pianobot


RAID_COLORS = {
    'Nest of the Grootslangs': 0x00AA00,
    'Orphion\'s Nexus of Light': 0xFFAA00,
    'The Canyon Colossus': 0x00AAAA,
    'The Nameless Anomaly': 0x5555FF,
}


async def guild_awards(bot: Pianobot) -> None:
    dt = datetime.now(timezone.utc)
    if (dt.day == 1 or dt.day == 15) and time(0, 0) <= dt.time() < time(0, 5):
        await update_for_cycle(bot, get_cycle(dt - timedelta(days=10)))
        results = await bot.database.guild_award_stats.get_for_cycle(get_cycle(dt - timedelta(days=10)))
        prev_results = await bot.database.guild_award_stats.get_for_cycle(get_cycle(dt - timedelta(days=20)))

        prev_raids = {entry.username: entry.raid_count for entry in prev_results}
        raid_res = [(entry.username, entry.raid_count - prev_raids.get(entry.username, 0)) for entry in results]
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
    prev_db_results = await bot.database.guild_award_stats.get_for_cycle(prev_cycle)
    prev_names = {entry.username for entry in prev_db_results}
    xp_per_raid = int(100 / 3 * (1.15 ** guild.level - 1))

    guild_raid_results: dict[str, list[str]] = {}
    guild_raid_extras: list[str] = []
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
            xp_diff = member.contributed_xp - db_stat.xp
            if member.is_online or member.contributed_xp != db_stat.xp:
                try:
                    player = await bot.corkus.player.getv3(member.uuid)
                    raids = player.get('globalData', {}).get('raids', {})
                    if raids.get('total', 0) != db_stat.raid_count:
                        await bot.database.guild_award_stats.update_raids(member.username, cycle, raids.get('list', {}))
                    wars = player.get('globalData', {}).get('wars', None)
                    if wars is not None and wars != db_stat.wars:
                        await bot.database.guild_award_stats.update_wars(member.username, cycle, wars)
                    if xp_diff >= xp_per_raid and xp_diff < 2 * xp_per_raid:
                        raid = next((r for r, c in raids.get('list', {}).items() if c - db_stat.raids[r] == 1), None)
                        if raid is not None:
                            guild_raid_results.setdefault(raid, []).append(member.username)
                        else:
                            guild_raid_extras.append(member.username)
                except CorkusException as e:
                    getLogger('tasks.guild_awards').warning(
                        'Error when fetching player data of `%s`: %s', member.username, e
                    )
                if member.contributed_xp != db_stat.xp:
                    await bot.database.guild_award_stats.update_xp(member.username, cycle, member.contributed_xp)

    for raid, members in guild_raid_results.items():
        for i in range(ceil(len(members) / 4)):
            current_members = members[i * 4: (i + 1) * 4]
            while len(current_members) < 4:
                try:
                    current_members.append(guild_raid_extras.pop())
                except IndexError:
                    break
            # await send_embed(bot, raid, current_members, guild.level)
    for i in range(ceil(len(guild_raid_extras) / 4)):
        current_members = guild_raid_extras[i * 4: (i + 1) * 4]
        # await send_embed(bot, None, current_members, guild.level)


async def send_embed(bot: Pianobot, raid: str | None, players: list[str], guild_level: int) -> None:
    file_aspect = File(f'assets/aspect.png', 'aspect.png')
    file_raid = File(f'assets/{raid}.png', 'raid.png')
    embed = Embed(
        color=RAID_COLORS.get(raid, None),
        title=':crossed_swords:   Guild Raid completed',
        description='\n'.join(f':number_{i + 1}:    {player}' for i, player in enumerate(players)),
    )
    embed.set_author(name=raid or 'Unknown Raid')
    embed.set_footer(
        text=f'+2 Aspects, +2048 Emeralds, +{display_short(400 / 3 * (1.15 ** guild_level - 1))} XP',
        icon_url='attachment://aspect.png',
    )
    embed.set_thumbnail(url='attachment://raid.png')
    webhook = Webhook.from_url(
        'https://discord.com/api/webhooks/1347509068176297984/IPbjbgIH-HuQIxUjbsULvT1mjKEn7G2i-IfBA1U_NdNqlnT001wRsbXmU-PhnOFU8rU7',
        session=bot.session,
    )
    await webhook.send(
        files=[file_aspect, file_raid],
        embed=embed,
        username='Eden Guild Raid Tracking',
        avatar_url='https://cdn.discordapp.com/avatars/861602324543307786/83f879567954aee29bc9fd534bc05b1f.webp'
    )


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
