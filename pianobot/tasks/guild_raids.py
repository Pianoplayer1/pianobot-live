from __future__ import annotations

from asyncio import gather, sleep
from logging import getLogger
from math import ceil
from typing import TYPE_CHECKING

from discord import Embed, File, Webhook

from corkus.objects import Member
from corkus.errors import CorkusException
from pianobot.utils import display_short as display

if TYPE_CHECKING:
    from pianobot import Pianobot


RAID_COLORS = {
    'Nest of the Grootslangs': 0x00AA00,
    'Orphion\'s Nexus of Light': 0xFFAA00,
    'The Canyon Colossus': 0x00AAAA,
    'The Nameless Anomaly': 0x5555FF,
}
WEBHOOK_URL = 'https://discord.com/api/webhooks/1347509068176297984/IPbjbgIH-HuQIxUjbsULvT1mjKEn7G2i-IfBA1U_NdNqlnT001wRsbXmU-PhnOFU8rU7'
AVATAR_URL = 'https://cdn.discordapp.com/avatars/861602324543307786/83f879567954aee29bc9fd534bc05b1f.webp'

async def guild_raids(bot: Pianobot) -> None:
    try:
        guild = await bot.corkus.guild.get('Eden')
    except CorkusException as e:
        getLogger('tasks.guild_awards').warning('Error when fetching guild data of `Eden`: %s', e)
        return

    db_stats = await bot.database.raid_members.get_all()
    potential_members = {}
    xp_per_raid = int(100 / 3 * (1.15 ** guild.level - 1))
    for member in guild.members:
        if member.uuid not in db_stats:
            raids = {}
            try:
                player = await bot.corkus.player.getv3(member.uuid)
                raids = player.get('globalData', {}).get('raids', {}).get('list', {})
            except CorkusException as e:
                getLogger('tasks.guild_awards').warning(
                    'Error when fetching player data of `%s`: %s', member.uuid, e
                )
            await bot.database.raid_members.add(member.uuid, member.contributed_xp)
            for raid, count in raids.items():
                await bot.database.raids.set(member.uuid, raid, count)
        else:
            xp_diff = member.contributed_xp - db_stats[member.uuid]
            if xp_diff > 0:
                await bot.database.raid_members.update_xp(member.uuid, member.contributed_xp)
                if xp_per_raid <= xp_diff < 3 * xp_per_raid:
                    member_raids = await bot.database.raids.get_for_player(member.uuid)
                    potential_members[member] = member_raids
            if xp_diff > 0 or member.is_online:
                try:
                    player = await bot.corkus.player.getv3(member.uuid)
                    raids = player.get('globalData', {}).get('raids', {}).get('list', {})
                except CorkusException as e:
                    getLogger('tasks.guild_awards').warning(
                        'Error when fetching player data of `%s`: %s', member.uuid, e
                    )
                    continue
                db_raids = await bot.database.raids.get_for_player(member.uuid)
                for raid, amount in raids.items():
                    if amount > db_raids.get(raid, 0):
                        await bot.database.raids.set(member.uuid, raid, amount)
    bot.loop.create_task(process_members(bot, potential_members, guild.level))


async def process_members(
        bot: Pianobot, potential_members: dict[Member, dict[str, int]], level: int
    ) -> None:
    results = await gather(*(process_one(bot, m, r) for m, r in potential_members.items()))
    raid_completions: dict[str, list[str]] = {}
    unknown: list[str] = []
    for member, raid in results:
        if raid is not None:
            raid_completions.setdefault(raid, []).append(member.username)
        else:
            unknown.append(member.username)
    add_unknown = len(unknown) == sum((4 - len(lst) % 4) % 4 for lst in raid_completions.values())
    for raid, members in raid_completions.items():
        for i in range(ceil(len(members) / 4)):
            current_members = members[i * 4: (i + 1) * 4]
            while add_unknown and len(current_members) < 4:
                current_members.append(unknown.pop())
            await send_embed(bot, raid, current_members, level)


async def process_one(
        bot: Pianobot, member: Member, old_raids: dict[str, int], tries: int = 0
    ) -> tuple[Member, str | None]:
    response = await bot.session.get(f'https://api.wynncraft.com/v3/player/{member.uuid}')
    if response.status != 200:
        return await process_one(bot, member, old_raids, tries + 1)
    data = await response.json()
    raids = data.get('globalData', {}).get('raids', {}).get('list', {})
    if sum(raids.values()) == sum(old_raids.values()):
        if tries >= 2:
            return member, None
        age = int(response.headers.get('Age', '0'))
        await sleep(121 - age)
        return await process_one(bot, member, old_raids, tries + 1)
    return member, next(r for r, c in raids.items() if c - old_raids.get(r, 0) == 1)


async def send_embed(bot: Pianobot, raid: str, players: list[str], guild_level: int) -> None:
    embed = Embed(
        color=RAID_COLORS.get(raid, None),
        title=':crossed_swords:   Guild Raid completed',
        description='\n'.join(f':number_{i + 1}:    {player}' for i, player in enumerate(players)),
    )
    embed.set_author(name=raid)
    embed.set_footer(
        text=f'+2 Aspects, +2048 Emeralds, +{display(400 / 3 * (1.15 ** guild_level - 1))} XP',
        icon_url='attachment://aspect.png',
    )
    embed.set_thumbnail(url='attachment://raid.png')
    await Webhook.from_url(WEBHOOK_URL, session=bot.session).send(
        files=[File('assets/aspect.png', 'aspect.png'), File(f'assets/{raid}.png', 'raid.png')],
        embed=embed,
        username='Eden Guild Raid Tracking',
        avatar_url=AVATAR_URL,
    )
