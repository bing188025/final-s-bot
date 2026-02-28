"""
Discord Welcome Bot
Sends a welcome card with the new member's avatar when someone joins the server.
"""

import os
import sys
import discord
import aiohttp

from config import BOT_TOKEN, WELCOME_CHANNEL_ID
from welcome_card import create_welcome_card

LOCK_FILE = "bot.lock"
BANNED_WORDS_FILE = "banned_words.txt"

# Load banned words from file
# Returns dict of {word: action} where action is "warn", "kick", or "ban"
def load_banned_words() -> dict[str, str]:
    if not os.path.exists(BANNED_WORDS_FILE):
        return {}
    result = {}
    with open(BANNED_WORDS_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                word, action = line.rsplit(":", 1)
                action = action.strip().lower()
            else:
                word, action = line, "warn"
            word = word.strip().lower()
            if action in ("warn", "kick", "ban"):
                result[word] = action
    return result

banned_words = load_banned_words()

# Track warning count per user: {user_id: warning_count}
warning_counts: dict[int, int] = {}

WARN_KICK_THRESHOLD = 3

# Prevent multiple instances from running at the same time
if os.path.exists(LOCK_FILE):
    with open(LOCK_FILE) as f:
        existing_pid = f.read().strip()
    print(f"[ERROR] Bot is already running (PID {existing_pid}). Only one instance is allowed.")
    sys.exit(1)

with open(LOCK_FILE, "w") as f:
    f.write(str(os.getpid()))


intents = discord.Intents.default()
intents.members = True         # Required to receive member join events
intents.message_content = True # Required to read message content

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Bot is online as {client.user} (ID: {client.user.id})")
    print(f"Welcome channel ID: {WELCOME_CHANNEL_ID}")
    if client.guilds:
        print("Connected to servers:")
        for guild in client.guilds:
            print(f"  - {guild.name} (ID: {guild.id})")
    else:
        print("[WARNING] Bot is not in any server. Invite it using the OAuth2 URL from the Developer Portal.")
    print("------")


@client.event
async def on_member_join(member: discord.Member):
    """Triggered when a new member joins the server."""
    channel = client.get_channel(WELCOME_CHANNEL_ID)
    if channel is None:
        print(f"[ERROR] Welcome channel {WELCOME_CHANNEL_ID} not found.")
        return

    # Download the member's avatar
    avatar_url = member.display_avatar.with_size(256).url
    async with aiohttp.ClientSession() as session:
        async with session.get(avatar_url) as resp:
            if resp.status != 200:
                print(f"[ERROR] Failed to download avatar for {member}.")
                return
            avatar_bytes = await resp.read()

    # Generate the welcome card
    member_count = member.guild.member_count
    card_buffer = create_welcome_card(
        username=member.display_name,
        avatar_bytes=avatar_bytes,
        member_count=member_count,
    )

    # Send the welcome message with the card image
    file = discord.File(fp=card_buffer, filename="welcome.png")
    await channel.send(
        content=f"Hey {member.mention} welcome to **{member.guild.name}**!",
        file=file,
    )
    print(f"[INFO] Welcomed {member.name} (#{member_count})")


@client.event
async def on_message(message: discord.Message):
    """Triggered when a message is sent in any channel."""
    if message.author.bot:
        return

    content_lower = message.content.lower()
    matched_action = None
    for word, action in banned_words.items():
        if word in content_lower:
            matched_action = action
            break

    if matched_action is None:
        return

    member = message.author
    await message.delete()

    if matched_action == "ban":
        await message.channel.send(f"{member.mention} You have been banned for using a prohibited word.")
        await member.ban(reason="Used a banned word with ban action.")
        warning_counts.pop(member.id, None)
        print(f"[MOD] Banned {member.name} for using a banned word.")

    elif matched_action == "kick":
        await message.channel.send(f"{member.mention} You have been kicked for using a prohibited word.")
        await member.kick(reason="Used a banned word with kick action.")
        warning_counts.pop(member.id, None)
        print(f"[MOD] Kicked {member.name} for using a banned word.")

    else:  # warn
        warning_counts[member.id] = warning_counts.get(member.id, 0) + 1
        count = warning_counts[member.id]

        if count >= WARN_KICK_THRESHOLD:
            await message.channel.send(
                f"{member.mention} You have been kicked after receiving {WARN_KICK_THRESHOLD} warnings."
            )
            await member.kick(reason=f"Received {WARN_KICK_THRESHOLD} warnings for banned words.")
            warning_counts.pop(member.id, None)
            print(f"[MOD] Kicked {member.name} after {WARN_KICK_THRESHOLD} warnings.")
        else:
            await message.channel.send(
                f"{member.mention} Warning {count}/{WARN_KICK_THRESHOLD}: your message contained a banned word. "
                f"You will be kicked after {WARN_KICK_THRESHOLD} warnings."
            )
            print(f"[MOD] Warned {member.name} ({count}/{WARN_KICK_THRESHOLD}).")


if __name__ == "__main__":
    try:
        client.run(BOT_TOKEN)
    finally:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
