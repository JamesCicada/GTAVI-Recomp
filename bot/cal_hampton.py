"""Cal Hampton, the project's Discord bot.

Slash commands:
    /progress        Roadmap, shader and library progress, from the published
                     progress page's progress.json.
    /faq [topic]     An answer from the FAQ in docs/community/discord.md on
                     GitHub, or the list of questions.
    /updates         Give yourself, or remove, the Updates role that is pinged
                     for announcements.

Configuration comes from environment variables, never from the repository:
    DISCORD_BOT_TOKEN   the bot token (required)
    DISCORD_GUILD_ID    server to register commands in instantly
                        (default: the project server)

Data is fetched over HTTPS and cached for a few minutes, so the bot needs no
checkout of the repository and always shows what is on main.
"""

from __future__ import annotations

import logging
import os
import re
import sys
import time

import aiohttp
import discord
from discord import app_commands

LOG = logging.getLogger("cal_hampton")

DEFAULT_GUILD = 1573077095201120322
SITE_URL = "https://jamescicada.github.io/GTAVI-Recomp/"
PROGRESS_URL = SITE_URL + "progress.json"
FAQ_URL = "https://raw.githubusercontent.com/JamesCicada/GTAVI-Recomp/main/docs/community/discord.md"
REPO_URL = "https://github.com/JamesCicada/GTAVI-Recomp"
UPDATES_ROLE = "Updates"
CACHE_SECONDS = 300
COLOUR = 0x2F81F7
BAR_WIDTH = 16


# --------------------------------------------------------------------------
# Data


class Cached:
    """Fetches a URL and keeps the parsed result for CACHE_SECONDS."""

    def __init__(self, url: str, parse):
        self.url = url
        self.parse = parse
        self.value = None
        self.fetched = 0.0

    async def get(self, session: aiohttp.ClientSession):
        if self.value is not None and time.monotonic() - self.fetched < CACHE_SECONDS:
            return self.value
        try:
            async with session.get(self.url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                response.raise_for_status()
                text = await response.text()
            self.value = self.parse(text)
            self.fetched = time.monotonic()
        except Exception:
            LOG.exception("Could not fetch %s", self.url)
            if self.value is None:
                raise
            # Keep serving the last good copy if a refresh fails.
        return self.value


def parse_progress(text: str) -> dict:
    import json

    return json.loads(text)


def parse_faq(markdown: str) -> list[tuple[str, str]]:
    """(question, answer) pairs from the FAQ blockquote in discord.md."""
    match = re.search(r"^## FAQ\n(.*?)(?=^## |\Z)", markdown, re.M | re.S)
    if not match:
        raise ValueError("no FAQ section")
    quoted = [line[1:].lstrip() if line.startswith(">") else None for line in match.group(1).splitlines()]
    text = "\n".join(line for line in quoted if line is not None).strip()

    pairs = []
    for block in text.split("\n\n"):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        head = re.match(r"^\*\*(.+?)\*\*\s*(.*)$", lines[0])
        if not head:
            continue
        question = head.group(1).strip()
        answer = " ".join(([head.group(2)] if head.group(2) else []) + lines[1:]).strip()
        pairs.append((question, answer))
    return pairs


def find_faq(pairs: list[tuple[str, str]], topic: str) -> tuple[str, str] | None:
    """Exact question first, then the question sharing the most words."""
    wanted = topic.strip().lower()
    for question, answer in pairs:
        if question.lower() == wanted:
            return question, answer
    words = set(re.findall(r"[a-z0-9]+", wanted))
    best, best_score = None, 0
    for question, answer in pairs:
        score = len(words & set(re.findall(r"[a-z0-9]+", question.lower())))
        if score > best_score:
            best, best_score = (question, answer), score
    return best


# --------------------------------------------------------------------------
# Formatting


def percent(done: int, total: int) -> int:
    return round(100 * done / total) if total else 0


def bar(done: int, total: int, blocked: int = 0) -> str:
    if not total:
        return "░" * BAR_WIDTH
    done_cells = round(BAR_WIDTH * done / total)
    if done and not done_cells:
        done_cells = 1
    if done < total and done_cells == BAR_WIDTH:
        done_cells = BAR_WIDTH - 1
    blocked_cells = min(round(BAR_WIDTH * blocked / total), BAR_WIDTH - done_cells)
    if blocked and not blocked_cells and done_cells < BAR_WIDTH:
        blocked_cells = 1
    return "█" * done_cells + "░" * (BAR_WIDTH - done_cells - blocked_cells) + "▒" * blocked_cells


def progress_embed(data: dict) -> discord.Embed:
    roadmap = data["roadmap"]
    done, blocked = roadmap["done"], roadmap["blocked"]
    total = done + roadmap["open"] + blocked
    upstream = data["anyps5"]
    shaders = upstream["shaders"]
    libs = upstream["libraries"]

    embed = discord.Embed(
        title="GTA VI Translation Layer: progress",
        url=SITE_URL,
        colour=COLOUR,
        description=(
            f"**Roadmap:** {done} / {total} tasks done ({percent(done, total)}%), "
            f"{blocked} blocked until the game files can be researched."
        ),
    )

    phase_lines = []
    for p in roadmap["phases"]:
        p_total = p["done"] + p["open"] + p["blocked"]
        short = p["title"].split(" ")[0].rstrip(",")
        phase_lines.append(
            f"{bar(p['done'], p_total, p['blocked'])} {percent(p['done'], p_total):>3}%  {p['number']}. {short}"
        )
    embed.add_field(
        name="Phases (█ done · ░ open · ▒ blocked)",
        value="```\n" + "\n".join(phase_lines) + "\n```",
        inline=False,
    )

    shader_lines = [
        f"{bar(s['translated'], s['total'])} {percent(s['translated'], s['total']):>3}%  {label}"
        for label, s in (("RDNA 2", shaders["rdna2"]), ("gfx1013", shaders["gfx1013"]))
    ]
    embed.add_field(name="Shaders translated", value="```\n" + "\n".join(shader_lines) + "\n```", inline=False)

    lib_lines = [f"{bar(libs['done'], libs['total'])} {percent(libs['done'], libs['total']):>3}%  All"]
    for lib in upstream["core_libraries"]:
        lib_lines.append(f"{bar(lib['done'], lib['total'])} {percent(lib['done'], lib['total']):>3}%  {lib['role']}")
    embed.add_field(
        name=f"System library functions ({upstream['library_count']} libraries)",
        value="```\n" + "\n".join(lib_lines) + "\n```",
        inline=False,
    )

    embed.set_footer(text=f"AnyPS5 {upstream['commit'][:7]} · counted from source code, not from running the game")
    return embed


# --------------------------------------------------------------------------
# Bot


class CalHampton(discord.Client):
    def __init__(self, guild_id: int):
        super().__init__(intents=discord.Intents.default())
        self.guild = discord.Object(id=guild_id)
        self.tree = app_commands.CommandTree(self)
        self.session: aiohttp.ClientSession | None = None
        self.progress = Cached(PROGRESS_URL, parse_progress)
        self.faq = Cached(FAQ_URL, parse_faq)
        register_commands(self)

    async def setup_hook(self) -> None:
        self.session = aiohttp.ClientSession(headers={"User-Agent": "CalHampton (GTAVI-Recomp Discord bot)"})
        # Registering per server makes commands appear at once.
        self.tree.copy_global_to(guild=self.guild)
        synced = await self.tree.sync(guild=self.guild)
        LOG.info("Registered %d commands in server %s", len(synced), self.guild.id)

    async def close(self) -> None:
        if self.session:
            await self.session.close()
        await super().close()

    async def on_ready(self) -> None:
        LOG.info("Logged in as %s", self.user)


def register_commands(bot: CalHampton) -> None:
    tree = bot.tree

    @tree.command(name="progress", description="Roadmap, shader and library progress")
    @app_commands.guild_only()
    async def progress(interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)
        try:
            data = await bot.progress.get(bot.session)
        except Exception:
            await interaction.followup.send(f"I couldn't load the numbers right now. See {SITE_URL}")
            return
        await interaction.followup.send(embed=progress_embed(data))

    @tree.command(name="faq", description="Answer a frequently asked question")
    @app_commands.describe(topic="The question, or a few words from it. Leave empty to list them.")
    @app_commands.guild_only()
    async def faq(interaction: discord.Interaction, topic: str | None = None) -> None:
        try:
            pairs = await bot.faq.get(bot.session)
        except Exception:
            await interaction.response.send_message("I couldn't load the FAQ right now. Try `#faq`.", ephemeral=True)
            return

        if not topic:
            listing = "\n".join(f"• {q}" for q, _ in pairs)
            embed = discord.Embed(title="FAQ", colour=COLOUR, description=listing)
            embed.set_footer(text="Use /faq topic:<question> for an answer")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        found = find_faq(pairs, topic)
        if not found:
            await interaction.response.send_message(
                "I don't have an answer for that. Try `/faq` to see the questions, or ask in `#general`.",
                ephemeral=True,
            )
            return
        question, answer = found
        await interaction.response.send_message(
            embed=discord.Embed(title=question, description=answer, colour=COLOUR),
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @faq.autocomplete("topic")
    async def faq_topics(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        try:
            pairs = await bot.faq.get(bot.session)
        except Exception:
            return []
        current = current.lower()
        return [
            app_commands.Choice(name=q[:100], value=q[:100])
            for q, _ in pairs
            if current in q.lower()
        ][:25]

    @tree.command(name="updates", description="Turn announcement pings on or off for yourself")
    @app_commands.guild_only()
    async def updates(interaction: discord.Interaction) -> None:
        member = interaction.user
        role = discord.utils.get(interaction.guild.roles, name=UPDATES_ROLE)
        if role is None or not isinstance(member, discord.Member):
            await interaction.response.send_message("The Updates role doesn't exist on this server.", ephemeral=True)
            return
        try:
            if role in member.roles:
                await member.remove_roles(role, reason="/updates")
                message = "Done: you won't be pinged for announcements any more. Run `/updates` again to turn it back on."
            else:
                await member.add_roles(role, reason="/updates")
                message = "Done: you'll be pinged for announcements. Run `/updates` again to turn it off."
        except discord.Forbidden:
            LOG.warning("Missing permission to manage the %s role", UPDATES_ROLE)
            message = "I'm not allowed to change that role. A moderator needs to move my role above Updates."
        await interaction.response.send_message(message, ephemeral=True)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    token = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
    if not token:
        print("Set DISCORD_BOT_TOKEN (see bot/README.md).", file=sys.stderr)
        return 1
    guild_id = int(os.environ.get("DISCORD_GUILD_ID", DEFAULT_GUILD))
    CalHampton(guild_id).run(token, log_handler=None)
    return 0


if __name__ == "__main__":
    sys.exit(main())
