"""
Discord Bot — CrowdWorks email notification.
"""

import asyncio
import os
import sys

# Fix Unicode output on Windows console
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import discord
from discord.ext import tasks

from config import BOT_TOKEN, CROWDWORKS_CHANNEL_ID, EMAIL_ADDRESS, EMAIL_PASSWORD, IMAP_SERVER
from crowdworks_notifier import fetch_new_crowdworks_messages

LOCK_FILE = "bot.lock"

# Prevent multiple instances — only block if the stored PID is actually alive
if os.path.exists(LOCK_FILE):
    with open(LOCK_FILE) as f:
        existing_pid = f.read().strip()
    pid_alive = False
    if existing_pid.isdigit():
        try:
            os.kill(int(existing_pid), 0)
            pid_alive = True
        except OSError:
            pass
    if pid_alive:
        print(f"[ERROR] Bot is already running (PID {existing_pid}). Only one instance is allowed.")
        sys.exit(1)
    else:
        print(f"[INFO] Stale lock file found (PID {existing_pid} is not running). Removing it.")

with open(LOCK_FILE, "w") as f:
    f.write(str(os.getpid()))


intents = discord.Intents.default()

client = discord.Client(intents=intents)


@tasks.loop(seconds=60)
async def check_crowdworks_emails():
    """Poll Gmail every 60 seconds for unread CrowdWorks notification emails."""
    try:
        channel = client.get_channel(CROWDWORKS_CHANNEL_ID)
        if channel is None:
            print(f"[CROWDWORKS] Channel {CROWDWORKS_CHANNEL_ID} not found.")
            return

        messages = await asyncio.to_thread(
            fetch_new_crowdworks_messages, IMAP_SERVER, EMAIL_ADDRESS, EMAIL_PASSWORD
        )

        for msg in messages:
            embed = discord.Embed(
                title=msg["subject"] or "CrowdWorks Message",
                description=msg["body"][:2000] if msg["body"] else "(No content)",
                color=0x00b4d8,
            )
            embed.set_author(name="CrowdWorks Notification")
            embed.add_field(name="From", value=msg["sender"], inline=True)
            embed.add_field(name="Date", value=msg["date"], inline=True)
            await channel.send(embed=embed)
            print(f"[CROWDWORKS] Posted notification: {msg['subject']}")
    except Exception as e:
        print(f"[CROWDWORKS] Error in check loop: {e}")


@client.event
async def on_ready():
    print(f"Bot is online as {client.user} (ID: {client.user.id})")
    if client.guilds:
        print("Connected to servers:")
        for guild in client.guilds:
            print(f"  - {guild.name} (ID: {guild.id})")
    else:
        print("[WARNING] Bot is not in any server.")
    if not check_crowdworks_emails.is_running():
        check_crowdworks_emails.start()
        print("[CROWDWORKS] Email polling started (every 60s).")
    print("------")


if __name__ == "__main__":
    import traceback
    try:
        client.run(BOT_TOKEN)
    except Exception as e:
        print(f"[FATAL] Bot crashed: {e}", flush=True)
        traceback.print_exc()
    finally:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
