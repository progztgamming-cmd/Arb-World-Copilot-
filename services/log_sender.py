from __future__ import annotations

from typing import Iterable

import discord


async def get_text_channel(bot: discord.Client, channel_id: int) -> discord.TextChannel | None:
    channel = bot.get_channel(channel_id)
    if isinstance(channel, discord.TextChannel):
        return channel
    return None


def build_embed(
    title: str,
    description: str = "",
    color: discord.Color | None = None,
    fields: Iterable[tuple[str, str, bool]] | None = None,
    footer: str | None = None,
    thumbnail_url: str | None = None,
    author_name: str | None = None,
) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=description,
        color=color or discord.Color.blurple(),
    )

    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value or "None", inline=inline)

    if footer:
        embed.set_footer(text=footer)

    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)

    if author_name:
        embed.set_author(name=author_name)

    return embed


async def send_embed_to_channel(
    bot: discord.Client,
    channel_id: int,
    *,
    title: str,
    description: str = "",
    color: discord.Color | None = None,
    fields: Iterable[tuple[str, str, bool]] | None = None,
    footer: str | None = None,
    thumbnail_url: str | None = None,
    author_name: str | None = None,
) -> discord.Message | None:
    channel = await get_text_channel(bot, channel_id)
    if channel is None:
        return None

    embed = build_embed(
        title=title,
        description=description,
        color=color,
        fields=fields,
        footer=footer,
        thumbnail_url=thumbnail_url,
        author_name=author_name,
    )
    return await channel.send(embed=embed)


async def send_member_dm(
    member: discord.abc.Messageable,
    *,
    title: str,
    description: str = "",
    color: discord.Color | None = None,
    fields: Iterable[tuple[str, str, bool]] | None = None,
    footer: str | None = None,
    thumbnail_url: str | None = None,
) -> discord.Message | None:
    embed = build_embed(
        title=title,
        description=description,
        color=color,
        fields=fields,
        footer=footer,
        thumbnail_url=thumbnail_url,
    )
    try:
        return await member.send(embed=embed)
    except discord.Forbidden:
        return None
    except discord.HTTPException:
        return None
