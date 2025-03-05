from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from corkus.errors import CorkusException
from discord import Embed, Webhook
from discord.utils import format_dt

from pianobot.db.members import Member

if TYPE_CHECKING:
    from pianobot import Pianobot

RANKS = ['Recruit', 'Recruiter', 'Captain', 'Strategist', 'Chief', 'Owner']


async def members(bot: Pianobot) -> None:
    try:
        guild_members = (await bot.corkus.guild.get('Eden')).members
    except CorkusException as e:
        getLogger('tasks.members').warning('Error when fetching guild data of `Eden`: %s', e)
        return

    database_members = await bot.database.members.get_all()
    saved_members: dict[str, Member] = {member.uuid.hex: member for member in database_members}

    for corkus_member in guild_members:
        saved_member = saved_members.pop(corkus_member.uuid.hex, None)
        if saved_member is None:
            await bot.database.members.add(
                corkus_member.uuid,
                corkus_member.join_date,
                corkus_member.username,
                corkus_member.rank.name.capitalize(),
                corkus_member.contributed_xp,
            )
            embed_content = (
                f'{corkus_member.username} has joined Eden'
                f' {format_dt(corkus_member.join_date, "R")}\n\n'
            )
            try:
                player = await corkus_member.fetch_player()
                embed_content += (
                    f'First join: {format_dt(player.join_date)}\n'
                    f'Playtime: {round(player.playtime.hours(4.7))} hours\n'
                    f'Total level: {player.combined_level}'
                )
            except CorkusException as e:
                getLogger('tasks.members').warning(
                    'Error when fetching player data of `%s`: %s', corkus_member.username, e
                )

            await send_embed(
                bot,
                title=f'Guild Join: {corkus_member.username}',
                content=embed_content,
                color=0x00FF00,
                uuid=corkus_member.uuid.hex,
            )
        else:
            if corkus_member.username != saved_member.name:
                await bot.database.members.update_name(corkus_member.uuid, corkus_member.username)
                embed_content = (
                    f'{saved_member.name} has changed their name to {corkus_member.username}!\n\n'
                    f'Guild rank: {corkus_member.rank.name.capitalize()}\n'
                    f'Old name: {saved_member.name}\n'
                    f'New name: {corkus_member.username}'
                )
                await send_embed(
                    bot,
                    title=f'Name Change: {corkus_member.username}',
                    content=embed_content,
                    color=0x88FFFF,
                    uuid=corkus_member.uuid.hex,
                )
            if corkus_member.rank.name.capitalize() != saved_member.rank:
                new_rank = corkus_member.rank.name.capitalize()
                await bot.database.members.update_rank(corkus_member.uuid, new_rank)
                is_promotion = RANKS.index(new_rank) > RANKS.index(saved_member.rank)
                embed_content = (
                    f'{corkus_member.username} has been'
                    f' {"promoted" if is_promotion else "demoted"}!\n\n'
                    f'Old rank: {saved_member.rank}\n'
                    f'New rank: {new_rank}'
                )
                await send_embed(
                    bot,
                    title=(
                        f'Guild {"promotion" if is_promotion else "demotion"}:'
                        f' {corkus_member.username}'
                    ),
                    content=embed_content,
                    color=0x88FF88 if is_promotion else 0xFF8888,
                    uuid=corkus_member.uuid.hex,
                )
            if corkus_member.contributed_xp != saved_member.contributed_xp:
                await bot.database.members.update_contributed_xp(
                    corkus_member.uuid, corkus_member.contributed_xp
                )

    for uuid, member in saved_members.items():
        await bot.database.members.remove(
            next(m for m in database_members if m.uuid.hex == uuid).uuid
        )
        embed_content = (
            f'{member.name} has left Eden!\n\n'
            f'Joined at: {format_dt(member.join_date)}\n'
            f'Last rank: {member.rank}\n'
            f'XP contributed: {member.contributed_xp}'
        )
        await send_embed(
            bot,
            title=f'Guild Leave: {member.name}',
            content=embed_content,
            color=0xFF0000,
            uuid=uuid,
        )


async def send_embed(bot: Pianobot, *, title: str, content: str, color: int, uuid: str) -> None:
    embed = Embed(
        title=title,
        description=content,
        color=color,
    )
    embed.set_thumbnail(url=f'https://mc-heads.net/avatar/{uuid}')
    if bot.member_update_channel is not None:
        webhook = Webhook.from_url(bot.member_update_channel, session=bot.session)
        await webhook.send(embed=embed, username='Eden Guild Log', avatar_url='https://cdn.discordapp.com/avatars/861602324543307786/83f879567954aee29bc9fd534bc05b1f.webp')
