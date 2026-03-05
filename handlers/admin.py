"""
handlers/admin.py
─────────────────
Admin-only commands:
  /broadcast  — Send a message to all registered users
  /ban <id> [reason]  — Ban a user
  /unban <id>         — Unban a user
  /bannedlist         — List all banned users
  /botstats           — Bot usage statistics
  /restart            — Restart the bot process
  /setfsub <@channel|channel_id>  — Enable force-subscribe
  /delfsub            — Disable force-subscribe
"""

import os
import sys
import time
import asyncio
import logging

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import (
    UserIsBlocked, InputUserDeactivated, PeerIdInvalid, FloodWait
)

from db import (
    ban_user, unban_user, is_banned,
    get_all_users, total_users_count, total_banned_count,
    get_banned_users, set_force_sub, get_force_sub,
)

logger = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_admins() -> list[int]:
    """Parse ADMINS env var — comma or space-separated Telegram user IDs."""
    raw = os.environ.get("ADMINS", "")
    result = []
    for part in raw.replace(",", " ").split():
        try:
            result.append(int(part.strip()))
        except ValueError:
            pass
    return result


# Parse once at import time — env vars don't change at runtime
ADMIN_IDS: list[int] = _parse_admins()


def admin_filter(_, __, message: Message) -> bool:
    if not message.from_user:
        return False
    return message.from_user.id in ADMIN_IDS


is_admin = filters.create(admin_filter)


# ── /broadcast ────────────────────────────────────────────────────────────────

def register(app: Client):

    @app.on_message(filters.command("broadcast") & filters.private & is_admin)
    async def cmd_broadcast(client: Client, message: Message):
        # Must reply to the message to broadcast
        if not message.reply_to_message:
            await message.reply(
                "📢 **Broadcast**\n\n"
                "Reply to a message with `/broadcast` to send it to all users."
            )
            return

        b_msg = message.reply_to_message
        sts = await message.reply("📤 Broadcasting… please wait.")
        start = time.time()

        total  = await total_users_count()
        done   = success = blocked = deleted = failed = 0

        async for user in get_all_users():
            uid = user.get("telegram_id")
            if not uid:
                continue
            # Skip banned users
            banned, _ = await is_banned(uid)
            if banned:
                continue  # don't increment done — banned users aren't in the audience
            try:
                await b_msg.copy(uid)
                success += 1
            except UserIsBlocked:
                blocked += 1
            except InputUserDeactivated:
                deleted += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
                try:
                    await b_msg.copy(uid)
                    success += 1
                except Exception:
                    failed += 1
            except Exception as e:
                logger.warning("broadcast to %s failed: %s", uid, e)
                failed += 1

            done += 1
            await asyncio.sleep(0.05)   # ~20 msgs/sec — safe rate

            # Progress update every 25 users
            if done % 25 == 0:
                try:
                    await sts.edit(
                        f"📤 **Broadcasting…**\n\n"
                        f"Progress: `{done}` / `{total}`\n"
                        f"✅ Success: `{success}`\n"
                        f"🚫 Blocked: `{blocked}`\n"
                        f"❌ Deleted: `{deleted}`\n"
                        f"⚠️ Failed: `{failed}`"
                    )
                except Exception:
                    pass

        elapsed = round(time.time() - start, 1)
        await sts.edit(
            f"✅ **Broadcast Complete!**\n\n"
            f"⏱ Time: `{elapsed}s`\n"
            f"👥 Total: `{total}`\n"
            f"✅ Success: `{success}`\n"
            f"🚫 Blocked: `{blocked}`\n"
            f"❌ Deleted: `{deleted}`\n"
            f"⚠️ Failed: `{failed}`"
        )

    # ── /ban ──────────────────────────────────────────────────────────────────

    @app.on_message(filters.command("ban") & filters.private & is_admin)
    async def cmd_ban(client: Client, message: Message):
        args = message.command[1:]
        if not args:
            await message.reply(
                "Usage: `/ban <user_id> [reason]`\n\n"
                "Example: `/ban 123456789 Spamming`"
            )
            return
        try:
            uid = int(args[0])
        except ValueError:
            await message.reply("⚠️ Invalid user ID. Must be a number.")
            return

        if uid in ADMIN_IDS:
            await message.reply("❌ Cannot ban another admin.")
            return

        reason = " ".join(args[1:]) if len(args) > 1 else "No reason provided"
        ok = await ban_user(uid, reason)
        if ok:
            await message.reply(
                f"🚫 **User Banned**\n\n"
                f"👤 ID: `{uid}`\n"
                f"📝 Reason: {reason}"
            )
            # Notify the banned user
            try:
                await client.send_message(
                    uid,
                    f"🚫 **You have been banned from using this bot.**\n\n"
                    f"📝 Reason: _{reason}_\n\n"
                    f"If you think this is a mistake, contact support."
                )
            except Exception:
                pass
        else:
            await message.reply("❌ Failed to ban user. Try again.")

    # ── /unban ────────────────────────────────────────────────────────────────

    @app.on_message(filters.command("unban") & filters.private & is_admin)
    async def cmd_unban(client: Client, message: Message):
        args = message.command[1:]
        if not args:
            await message.reply("Usage: `/unban <user_id>`")
            return
        try:
            uid = int(args[0])
        except ValueError:
            await message.reply("⚠️ Invalid user ID.")
            return

        ok = await unban_user(uid)
        if ok:
            await message.reply(f"✅ User `{uid}` has been unbanned.")
            try:
                await client.send_message(uid, "✅ You have been unbanned! Use /start to continue.")
            except Exception:
                pass
        else:
            await message.reply(f"⚠️ User `{uid}` was not found in the banned list.")

    # ── /bannedlist ───────────────────────────────────────────────────────────

    @app.on_message(filters.command("bannedlist") & filters.private & is_admin)
    async def cmd_bannedlist(client: Client, message: Message):
        count = await total_banned_count()
        if count == 0:
            await message.reply("✅ No banned users.")
            return

        lines = [f"🚫 **Banned Users** ({count})\n"]
        async for user in get_banned_users():
            uid    = user.get("telegram_id", "?")
            reason = user.get("ban_reason", "—")
            lines.append(f"• `{uid}` — {reason}")

        text = "\n".join(lines)
        # Telegram message limit
        if len(text) > 4000:
            # Send as file
            fname = "/tmp/banned_users.txt"
            with open(fname, "w") as f:
                f.write("\n".join(lines))
            await message.reply_document(fname, caption="🚫 Banned users list")
            os.remove(fname)
        else:
            await message.reply(text)

    # ── /stats ────────────────────────────────────────────────────────────────

    @app.on_message(filters.command("botstats") & filters.private & is_admin)
    async def cmd_botstats(client: Client, message: Message):
        total  = await total_users_count()
        banned = await total_banned_count()
        active = total - banned
        fsub   = await get_force_sub() or "Disabled"

        await message.reply(
            f"📊 **Bot Statistics**\n\n"
            f"👥 Total Users: `{total}`\n"
            f"✅ Active: `{active}`\n"
            f"🚫 Banned: `{banned}`\n\n"
            f"📢 Force Subscribe: `{fsub}`"
        )

    # ── /restart ──────────────────────────────────────────────────────────────

    @app.on_message(filters.command("restart") & filters.private & is_admin)
    async def cmd_restart(client: Client, message: Message):
        msg = await message.reply("🔄 **Restarting bot…**")
        await asyncio.sleep(1)
        await msg.edit("✅ **Restarting now!**")
        os.execl(sys.executable, sys.executable, *sys.argv)

    # ── /setfsub / /delfsub ───────────────────────────────────────────────────

    @app.on_message(filters.command("setfsub") & filters.private & is_admin)
    async def cmd_setfsub(client: Client, message: Message):
        args = message.command[1:]
        if not args:
            current = await get_force_sub() or "Disabled"
            await message.reply(
                f"📢 **Force Subscribe**\n\n"
                f"Current: `{current}`\n\n"
                f"Usage: `/setfsub @yourchannel`\n"
                f"Or use channel ID: `/setfsub -1001234567890`\n\n"
                f"To disable: `/delfsub`\n\n"
                f"⚠️ Make sure the bot is an **admin** in the channel."
            )
            return
        channel = args[0].strip()
        # Validate — must be @username or negative channel ID, not a phone number
        ch = channel.lstrip("@")
        if channel.startswith("+") or (ch.isdigit() and not channel.startswith("-")):
            await message.reply(
                "⚠️ **Invalid channel format.**\n\n"
                "Please use:\n"
                "• Username: `/setfsub @yourchannel`\n"
                "• Channel ID: `/setfsub -1001234567890`\n\n"
                "Phone numbers are not supported."
            )
            return
        ok = await set_force_sub(channel)
        if ok:
            await message.reply(
                f"✅ **Force Subscribe Enabled**\n\n"
                f"Channel: `{channel}`\n\n"
                f"Users must join this channel to use the bot.\n"
                f"Use `/delfsub` to disable."
            )
        else:
            await message.reply("❌ Failed to save. Try again.")

    @app.on_message(filters.command("delfsub") & filters.private & is_admin)
    async def cmd_delfsub(client: Client, message: Message):
        ok = await set_force_sub(None)
        if ok:
            await message.reply("✅ **Force Subscribe Disabled.**\n\nAll users can now use the bot freely.")
        else:
            await message.reply("❌ Failed. Try again.")
