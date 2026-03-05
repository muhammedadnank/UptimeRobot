"""
handlers/inline.py
──────────────────
Inline mode: @botusername <query>

Users can search their monitors inline from any chat.
Results show monitor status, uptime, and response time.

Usage:
  @botusername            → show all monitors
  @botusername mysite     → filter monitors by name
  @botusername down       → show only down monitors
  @botusername up         → show only up monitors
  @botusername paused     → show only paused monitors
"""

import logging
from pyrogram import Client
from pyrogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from app.core.api_cache import get_api_for
from app.core.db import is_banned

logger = logging.getLogger(__name__)

STATUS_EMOJI = {0: "⏸️", 1: "🔍", 2: "✅", 8: "🟡", 9: "🔴"}
STATUS_TEXT  = {0: "Paused", 1: "Not Checked", 2: "Up", 8: "Seems Down", 9: "Down"}
TYPE_TEXT    = {1: "HTTP(s)", 2: "Keyword", 3: "Ping", 4: "Port", 5: "Heartbeat"}

# Status filter keywords users can type
STATUS_FILTERS = {
    "up":     [2],
    "down":   [9, 8],
    "paused": [0],
    "all":    [0, 1, 2, 8, 9],
}


def _monitor_to_article(m: dict, idx: int) -> InlineQueryResultArticle:
    """Convert a monitor dict into an InlineQueryResultArticle."""
    status  = m.get("status", 1)
    emoji   = STATUS_EMOJI.get(status, "❓")
    label   = STATUS_TEXT.get(status, "Unknown")
    name    = m.get("friendly_name", m.get("url", "Unknown"))
    url     = m.get("url", "")
    mid     = m.get("id", "")
    mtype   = TYPE_TEXT.get(m.get("type", 1), "Unknown")

    # Uptime ratios — only present if fetched with custom_uptime_ratios param
    ratios  = m.get("custom_uptime_ratio", "").split("-")
    r7      = f"{ratios[0]}%" if len(ratios) > 0 and ratios[0] else "N/A"
    r30     = f"{ratios[1]}%" if len(ratios) > 1 and ratios[1] else "N/A"

    # Response time — last recorded value
    rt_data = m.get("response_times", [])
    if rt_data:
        vals   = [r["value"] for r in rt_data if r.get("value")]
        avg_rt = f"{round(sum(vals)/len(vals))} ms" if vals else "N/A"
    else:
        avg_rt = "N/A"

    # Message content that gets sent when user picks this result
    msg_text = (
        f"{emoji} **{name}** — {label}\n\n"
        f"🔗 URL: `{url}`\n"
        f"🔧 Type: {mtype}\n"
        f"🆔 ID: `{mid}`\n\n"
        f"⏱ Avg Response: `{avg_rt}`\n"
        f"📈 Uptime 7d: `{r7}` | 30d: `{r30}`\n\n"
        f"_Checked via @UptimeRobot Bot_"
    )

    # Short description shown in the inline result list
    desc = f"{label}  •  7d: {r7}  •  {avg_rt}"
    if url:
        desc = f"{url[:40]}{'…' if len(url)>40 else ''}  •  {label}"

    return InlineQueryResultArticle(
        id=str(idx),
        title=f"{emoji}  {name}",
        description=desc,
        input_message_content=InputTextMessageContent(msg_text),
    )


def register(app: Client):

    @app.on_inline_query()
    async def handle_inline(client: Client, query: InlineQuery):
        uid = query.from_user.id

        # Ban check — banned users get a single error result
        banned, reason = await is_banned(uid)
        if banned:
            await query.answer(
                results=[
                    InlineQueryResultArticle(
                        id="banned",
                        title="🚫 You are banned",
                        description=f"Reason: {reason}",
                        input_message_content=InputTextMessageContent(
                            f"🚫 You are banned from this bot.\nReason: {reason}"
                        ),
                    )
                ],
                cache_time=5,
            )
            return

        # API key check
        api = await get_api_for(uid)
        if not api:
            await query.answer(
                results=[
                    InlineQueryResultArticle(
                        id="no_key",
                        title="🔑 No API key set",
                        description="Open the bot and use /setkey to link your UptimeRobot account.",
                        input_message_content=InputTextMessageContent(
                            "🔑 No UptimeRobot API key set.\n\n"
                            "Open the bot and use `/setkey ur_your_key` to get started."
                        ),
                    )
                ],
                cache_time=5,
            )
            return

        search_text = (query.query or "").strip().lower()

        try:
            monitors = await api.get_monitors(
                response_times=1,
                custom_uptime_ratios="7-30",
            )
        except Exception as e:
            logger.warning("inline: get_monitors failed for user %s: %s", uid, e)
            monitors = []

        if not monitors:
            await query.answer(
                results=[
                    InlineQueryResultArticle(
                        id="no_monitors",
                        title="📭 No monitors found",
                        description="Add monitors at dashboard.uptimerobot.com",
                        input_message_content=InputTextMessageContent(
                            "📭 No monitors found in your UptimeRobot account."
                        ),
                    )
                ],
                cache_time=10,
            )
            return

        # ── Filter logic ──────────────────────────────────────────────────────
        filtered = monitors

        if search_text in STATUS_FILTERS:
            # e.g. "up", "down", "paused", "all"
            allowed = STATUS_FILTERS[search_text]
            filtered = [m for m in monitors if m.get("status", 1) in allowed]
        elif search_text:
            # Text search on friendly_name and url
            filtered = [
                m for m in monitors
                if search_text in m.get("friendly_name", "").lower()
                or search_text in m.get("url", "").lower()
            ]

        if not filtered:
            await query.answer(
                results=[
                    InlineQueryResultArticle(
                        id="no_match",
                        title=f"🔍 No monitors match '{query.query}'",
                        description="Try: 'up', 'down', 'paused', or a monitor name",
                        input_message_content=InputTextMessageContent(
                            f"No monitors match **{query.query}**.\n\n"
                            "Tips:\n"
                            "• Type `up` / `down` / `paused` to filter by status\n"
                            "• Type part of the monitor name to search"
                        ),
                    )
                ],
                cache_time=5,
            )
            return

        # Telegram allows max 50 inline results
        results = [
            _monitor_to_article(m, i)
            for i, m in enumerate(filtered[:50])
        ]

        # Summary article at the top when showing all / filtered by status
        if not search_text or search_text in STATUS_FILTERS:
            up     = sum(1 for m in monitors if m.get("status") == 2)
            down   = sum(1 for m in monitors if m.get("status") in (8, 9))
            paused = sum(1 for m in monitors if m.get("status") == 0)
            summary_text = (
                f"📊 **Monitor Overview**\n\n"
                f"✅ Up: `{up}`  🔴 Down: `{down}`  ⏸️ Paused: `{paused}`\n"
                f"📋 Total: `{len(monitors)}`\n\n"
                f"_Checked via @UptimeRobot Bot_"
            )
            summary = InlineQueryResultArticle(
                id="summary",
                title=f"📊  Overview — {up}✅ {down}🔴 {paused}⏸️",
                description=f"{len(monitors)} monitors total · Tap to share summary",
                input_message_content=InputTextMessageContent(summary_text),
            )
            results.insert(0, summary)

        await query.answer(results=results, cache_time=10)
