import discord


# ============================================================
# STRAW HAT COLOURS
# ============================================================

RED = discord.Color.from_rgb(220, 38, 38)
YELLOW = discord.Color.from_rgb(234, 179, 8)
GREEN = discord.Color.from_rgb(34, 197, 94)
BLUE = discord.Color.from_rgb(37, 99, 235)


# ============================================================
# BASE EMBED
# ============================================================

def create_embed(
    title: str,
    description: str | None = None,
    color: discord.Color = RED,
    banner_url: str | None = None,
    thumbnail_url: str | None = None,
    footer_text: str = "Straw Hat • Discord Bot",
    timestamp: bool = True,
) -> discord.Embed:

    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
    )

    if banner_url:
        embed.set_image(url=banner_url)

    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)

    if timestamp:
        embed.timestamp = discord.utils.utcnow()

    embed.set_footer(text=footer_text)

    return embed


# ============================================================
# SUCCESS EMBED
# ============================================================

def create_success_embed(
    title: str,
    description: str | None = None,
    banner_url: str | None = None,
) -> discord.Embed:

    return create_embed(
        title=title,
        description=description,
        color=GREEN,
        banner_url=banner_url,
        footer_text="Straw Hat • Success",
    )


# ============================================================
# WARNING EMBED
# ============================================================

def create_warning_embed(
    title: str,
    description: str | None = None,
    banner_url: str | None = None,
) -> discord.Embed:

    return create_embed(
        title=title,
        description=description,
        color=YELLOW,
        banner_url=banner_url,
        footer_text="Straw Hat • Warning",
    )


# ============================================================
# INFO EMBED
# ============================================================

def create_info_embed(
    title: str,
    description: str | None = None,
    banner_url: str | None = None,
) -> discord.Embed:

    return create_embed(
        title=title,
        description=description,
        color=BLUE,
        banner_url=banner_url,
        footer_text="Straw Hat • Information",
    )


# ============================================================
# ERROR EMBED
# ============================================================

def create_error_embed(
    title: str,
    description: str | None = None,
    banner_url: str | None = None,
) -> discord.Embed:

    return create_embed(
        title=title,
        description=description,
        color=RED,
        banner_url=banner_url,
        footer_text="Straw Hat • Error",
    )