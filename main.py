"""
ReelPilot — Telegram bot (polling mode) + Flask dashboard launcher.

Single process, two lightweight threads:
  * python-telegram-bot polling loop
  * Flask serving the mint dashboard on 0.0.0.0:8080

Memory discipline: no browsers, throttled progress edits, explicit
gc.collect() at the end of every video lifecycle, temp files deleted
immediately after upload.
"""

import asyncio
import html
import logging
import os
import threading

import config  # noqa: F401  (sets MALLOC_ARENA_MAX etc. at import time)
import database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("reelpilot.main")

# --- memory guards FIRST, then heavyweight imports -----------------------
os.environ.setdefault("MALLOC_ARENA_MAX", "2")

import ig_handler  # noqa: E402  (installs the browser-import guard)


def _startup() -> None:
    database.init_db()
    try:
        from PIL import Image  # warm Pillow once (kept off the request path)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Telegram handlers
# ---------------------------------------------------------------------------

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.constants import ParseMode, ChatAction
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

WELCOME = (
    "🛩 <b>Welcome to ReelPilot</b>\n\n"
    "Cross-post reels in one tap. Send me any Instagram, TikTok, Facebook or "
    "Threads link and I'll publish it to every active account.\n\n"
    "Type /help for the full command list."
)

HELP_TEXT = (
    "🛩 <b>ReelPilot — Command Guide</b>\n\n"
    "<b>Posting reels</b>\n"
    "• Send any Instagram / TikTok / Facebook / Threads video link.\n"
    "• I download it (16K-buffer streaming), then post sequentially to all "
    "active accounts with a random 3-7s delay between each.\n"
    "• A progress bar shows live status: <code>[████░░░░░░] 40%</code>\n\n"
    "<b>Custom thumbnail</b>\n"
    "• <code>/setthumb</code> — reply to a photo, or attach one, to set the "
    "global cover image (<code>/data/global_custom_thumb.jpg</code>).\n"
    "• <code>/delthumb</code> — delete the custom thumbnail.\n\n"
    "<b>Access</b>\n"
    "• New users are added to the approval queue and notified.\n"
    "• Admins approve or reject from the web dashboard.\n\n"
    "Sessions: Instagram via instagrapi HTTP session · TikTok via Netscape "
    "cookie text. No headless browsers, ever."
)


def progress_bar(pct: float, width: int = 10) -> str:
    """Render [████░░░░░░] 40% from a 0..1 fraction."""
    pct = max(0.0, min(1.0, pct))
    filled = int(round(pct * width))
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {int(pct * 100)}%"


def _dashboard_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🛩 Open Web Dashboard", url=config.WEBAPP_PUBLIC_URL)]]
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _startup_user_record(update)
    await update.message.reply_text(
        WELCOME, parse_mode=ParseMode.HTML, reply_markup=_dashboard_button()
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)


async def cmd_setthumb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Save the attached or replied-to photo as the global custom thumbnail."""
    photo = None
    if update.message and update.message.reply_to_message:
        photos = update.message.reply_to_message.photo
        if photos:
            photo = photos[-1]
    if photo is None and update.message and update.message.photo:
        photo = update.message.photo[-1]
    if photo is None:
        await update.message.reply_text(
            "📷 Send or reply to a photo with /setthumb to set the global "
            "custom thumbnail."
        )
        return
    file = await photo.get_file()
    # Stream the image to disk instead of holding it in RAM
    custom_dir = config.DATA_DIR
    custom_dir.mkdir(parents=True, exist_ok=True)
    await file.download_to_drive(config.THUMB_PATH)
    database.set_stat("custom_thumb", 1)
    await update.message.reply_text(
        f"✅ Custom thumbnail saved to <code>{html.escape(str(config.THUMB_PATH))}</code>",
        parse_mode=ParseMode.HTML,
    )


async def cmd_delthumb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if config.THUMB_PATH.exists():
        try:
            config.THUMB_PATH.unlink()
            database.set_stat("custom_thumb", 0)
            await update.message.reply_text("🗑 Custom thumbnail deleted.")
        except OSError:
            await update.message.reply_text("⚠️ Could not delete the thumbnail file.")
    else:
        await update.message.reply_text("No custom thumbnail is currently set.")


async def handle_photo_caption(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Photos captioned '/setthumb' arrive here (CommandHandler is text-only)."""
    caption = (update.message.caption or "").strip()
    if caption.lower().startswith("/setthumb"):
        await cmd_setthumb(update, context)


def _startup_user_record(update: Update) -> dict | None:
    """Upsert the sender into the users table; returns their row."""
    if not update.effective_user:
        return None
    u = update.effective_user
    status = database.upsert_user(
        u.id,
        u.username,
        u.first_name,
    )
    return database.get_user(u.id) or {"user_id": u.id, "status": status}


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Detect supported links and run the download → post-everywhere pipeline."""
    user = _startup_user_record(update)
    if not user:
        return
    text = update.message.text or update.message.caption or ""
    platform, url = config.detect_platform(text)
    if not platform:
        return  # not a supported link; ignore silently

    user_id = update.effective_user.id
    if user_id != config.SUPER_ADMIN_ID and user["status"] != "approved":
        await update.message.reply_text(
            "🚫 You're not approved yet. An admin will review your request "
            "from the web dashboard. You'll be notified once approved."
        )
        return

    await update.message.reply_chat_action(ChatAction.UPLOAD_VIDEO)

    status_msg = await update.message.reply_text(
        f"🛩 <b>ReelPilot</b> · {html.escape(platform.title())}\n"
        f"🔗 <code>{html.escape(url[:120])}</code>\n\n{progress_bar(0)}",
        parse_mode=ParseMode.HTML,
    )

    loop = asyncio.get_running_loop()

    def progress_cb(stage: str, detail: str, pct: float) -> None:
        """Thread-safe progress funnel → scheduled message edit."""
        if stage == "download":
            asyncio.run_coroutine_threadsafe(
                _edit_progress(status_msg, platform, detail, pct), loop
            ).result(timeout=5)
        elif stage == "account":
            asyncio.run_coroutine_threadsafe(
                _edit_progress(status_msg, platform, f"Posting → {detail}", pct), loop
            ).result(timeout=5)

    def run_pipeline() -> dict:
        return ig_handler.post_everywhere(url)

    future = loop.run_in_executor(None, run_pipeline)
    try:
        results = await future
    except ig_handler.DownloadError as exc:
        await status_msg.edit_text(
            f"⚠️ {html.escape(str(exc))}", parse_mode=ParseMode.HTML
        )
        return
    except Exception as exc:
        logger.exception("pipeline failed")
        await status_msg.edit_text(
            f"⚠️ Pipeline failed: {html.escape(str(exc)[:300])}",
            parse_mode=ParseMode.HTML,
        )
        return

    ok = sum(1 for v in results.values() if v.startswith("ok:"))
    failed = len(results) - ok
    lines = [
        f"🛩 <b>Done</b> · {html.escape(platform.title())}",
        "",
    ]
    accs = {a["id"]: a for a in database.all_accounts()}
    for acc_id, result in results.items():
        acc = accs.get(int(acc_id), {})
        name = html.escape(acc.get("username", "?"))
        plat = (acc.get("platform") or "?").upper()
        if result.startswith("ok:"):
            code = result.split(":", 1)[1]
            link = f"https://www.instagram.com/reel/{code}/" if plat == "INSTAGRAM" else code
            link_repr = (
                f'<a href="{link}">{html.escape(code[:24])}</a>' if plat == "INSTAGRAM" else html.escape(code[:24])
            )
            lines.append(f"✅ <b>{plat}</b> · {name} · {link_repr}")
        else:
            err = result.split(":", 1)[1]
            lines.append(f"❌ <b>{plat}</b> · {name} · {html.escape(err[:80])}")
    lines.append("")
    lines.append(f"<b>{ok}</b> posted · <b>{failed}</b> failed")
    try:
        await status_msg.edit_text("\n".join(lines), parse_mode=ParseMode.HTML)
    except Exception:
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
    import gc as _gc
    _gc.collect()


async def _edit_progress(status_msg, platform: str, detail: str, pct: float) -> None:
    """Throttled progress-bar edit ([████░░░░░░] 40%)."""
    try:
        await status_msg.edit_text(
            f"🛩 <b>ReelPilot</b> · {html.escape(platform.title())}\n"
            f"⚙️ {html.escape(detail)}\n\n{progress_bar(pct)}",
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass  # "message is not modified" and network blips are fine to skip


def run_bot() -> None:
    if not config.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set — bot loop disabled.")
        return

    async def _post_init(app: Application) -> None:
        await app.bot.set_my_commands(
            [
                BotCommand("start", "Welcome + dashboard link"),
                BotCommand("help", "How to post reels and set thumbnails"),
                BotCommand("setthumb", "Set the global custom thumbnail"),
                BotCommand("delthumb", "Delete the custom thumbnail"),
            ]
        )

    app = (
        ApplicationBuilder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .pool_timeout(10)
        .connect_timeout(10)
        .read_timeout(30)
        .write_timeout(30)
        .post_init(_post_init)
        .build()
    )
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("setthumb", cmd_setthumb))
    app.add_handler(CommandHandler("delthumb", cmd_delthumb))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo_caption))
    logger.info("Telegram polling started (super admin %s)", config.SUPER_ADMIN_ID)
    app.run_polling(drop_pending_updates=True, allowed_updates=None)


def main() -> None:
    _startup()
    # Dashboard runs in a daemon thread so the bot loop owns the process.
    from dashboard import run_dashboard

    threading.Thread(target=run_dashboard, name="flask", daemon=True).start()
    run_bot()
    logger.info("ReelPilot stopped.")


if __name__ == "__main__":
    main()
