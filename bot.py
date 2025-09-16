# bot.py
import logging
import asyncio
import os
from mega import Mega
from telegram import Update, ForceReply
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ConversationHandler, ContextTypes
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# conversation states
LOGIN_EMAIL, LOGIN_PASSWORD = range(2)

# in-memory sessions: {telegram_id: Mega() instance}
user_sessions = {}

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not set in env")
    raise SystemExit("Set TELEGRAM_BOT_TOKEN environment variable")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to MEGA Rename Bot\n\n"
        "Commands:\n"
        "/login - provide MEGA credentials (kept in memory during session)\n"
        "/rename_all <basename> - rename all files/folders to basename_index\n"
        "/cancel - cancel login flow\n\n"
        "After renaming you'll be automatically logged out."
    )

# LOGIN flow
async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please send your MEGA email:", reply_markup=ForceReply())
    return LOGIN_EMAIL

async def login_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mega_email'] = update.message.text.strip()
    await update.message.reply_text("Now send your MEGA password:", reply_markup=ForceReply())
    return LOGIN_PASSWORD

async def login_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = context.user_data.get('mega_email')
    password = update.message.text.strip()
    user_id = update.effective_user.id

    msg = await update.message.reply_text("🔐 Attempting to login to MEGA...")
    try:
        mega = Mega()
        m = mega.login(email, password)
        # quick check
        _ = m.get_files()
        user_sessions[user_id] = m
        await msg.edit_text("✅ Logged in to MEGA successfully. Now use /rename_all <basename>")
    except Exception as e:
        logger.exception("MEGA login failed")
        await msg.edit_text(f"❌ Login failed: {e}")
    return ConversationHandler.END

# RENAME
async def rename_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_sessions:
        await update.message.reply_text("⚠️ You must /login first.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /rename_all <basename>\nExample: /rename_all holiday")
        return

    base_name = context.args[0].strip()
    await update.message.reply_text(f"⏳ Starting rename to base '{base_name}'... (you will be logged out after completion)")

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, perform_rename, user_sessions[user_id], base_name)

    # logout and clear session
    try:
        user_sessions[user_id].logout()
    except Exception:
        pass
    user_sessions.pop(user_id, None)

    await update.message.reply_text(result + "\n\n🔒 Logged out from MEGA.")

def perform_rename(m, base_name: str) -> str:
    try:
        files = m.get_files()
    except Exception as e:
        logger.exception("Failed to get files")
        return f"Failed to list files: {e}"

    import os
    idx = 1
    renamed = 0
    failed = 0

    # files is dict-like: node_id -> meta
    for node_id, meta in list(files.items()):
        try:
            # meta might contain ['a']['n'] for the name
            orig_name = None
            if isinstance(meta, dict):
                a = meta.get('a')
                if isinstance(a, dict):
                    orig_name = a.get('n')
                if not orig_name:
                    orig_name = meta.get('n')
            if not orig_name:
                orig_name = f"node_{node_id}"

            root, ext = os.path.splitext(orig_name)
            if ext:
                new_name = f"{base_name}_{idx}{ext}"
            else:
                new_name = f"{base_name}_{idx}"

            # try rename
            try:
                m.rename(node_id, new_name)
            except Exception:
                m.rename(meta, new_name)  # fallback

            renamed += 1
            idx += 1
        except Exception as e:
            logger.warning("Failed rename for node %s: %s", node_id, e)
            failed += 1

    return f"✅ Rename completed. Renamed: {renamed}. Failed: {failed}."

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    login_conv = ConversationHandler(
        entry_points=[CommandHandler("login", login_command)],
        states={
            LOGIN_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_email)],
            LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(login_conv)
    app.add_handler(CommandHandler("rename_all", rename_all))
    app.add_handler(CommandHandler("cancel", cancel))

    logger.info("Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
