"""
handlers/middleware.py
──────────────────────
Reusable pre-checks applied in every command handler:
  - is_user_banned()   — check ban status before handling any message
  - check_force_sub()  — verify channel membership if force-sub is active
"""

import logging
from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, PeerIdInvalid

from db import is_banned, get_force_sub

logger = logging.getLogger(__name__)


async def check_banned(client: Client, message: Message) -> bool:
    """
    Returns True if the user is banned (caller should return early).
    Sends a denial message automatically.
    """
    if not message.from_user:
        return False
    banned, reason = await is_banned(message.from_user.id)
    if banned:
        await message.reply(
            f"🚫 **You are banned from using this bot.**\n\n"
            f"📝 Reason: _{reason}_\n\n"
            f"If you think this is a mistake, contact the bot admin."
        )
        return True
    return False


async def check_force_sub(client: Client, message: Message) -> bool:
    """
    Returns True if user is NOT subscribed and a message was sent (caller should return early).
    Returns False if force-sub is disabled or user is already a member.
    """
    channel = await get_force_sub()
    if not channel:
        return False  # feature disabled

    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return False

    try:
        member = await client.get_chat_member(channel, user_id)
        # Banned/kicked members should not pass
        from pyrogram.enums import ChatMemberStatus
        if member.status == ChatMemberStatus.BANNED:
            raise UserNotParticipant
        return False   # user is a member — all good
    except UserNotParticipant:
        # Build invite link
        try:
            invite = await client.create_chat_invite_link(channel)
            invite_url = invite.invite_link
        except Exception:
            # Fallback: use channel as username link
            ch = str(channel).lstrip("@")
            invite_url = f"https://t.me/{ch}" if not str(channel).lstrip("-").isdigit() else None

        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = []
        if invite_url:
            buttons.append([InlineKeyboardButton("📢 Join Channel", url=invite_url)])
        buttons.append([InlineKeyboardButton("🔄 I Joined — Try Again", callback_data="check_fsub")])

        await message.reply(
            "🛡️ **Access Restricted**\n\n"
            "You must join our channel to use this bot.\n\n"
            "👇 Join and then tap **I Joined — Try Again**.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return True
    except (ChatAdminRequired, PeerIdInvalid) as e:
        logger.warning("force_sub check failed (%s): %s — skipping check", channel, e)
        return False   # misconfigured channel, don't block users
    except Exception as e:
        logger.warning("force_sub unexpected error: %s", e)
        return False
