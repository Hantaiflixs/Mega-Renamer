import os
import logging
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from mega import Mega
from pymongo import MongoClient

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app for health check
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Mega Rename Bot Running!", 200

# ENV
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

# DB setup
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["mega_bot"]
sessions = db["sessions"]

# Telegram App
application = Application.builder().token(BOT_TOKEN).build()

# Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome!\nUse /login <email> <password> to login.")

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /login <email> <password>")
        return
    email, password = context.args[0], context.args[1]
    try:
        mega = Mega()
        m = mega.login(email, password)
        if not m:
            await update.message.reply_text("❌ Login failed!")
            return
        sessions.update_one(
            {"user_id": update.effective_user.id},
            {"$set": {"email": email, "password": password}},
            upsert=True
        )
        await update.message.reply_text("✅ Logged in successfully!")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

async def rename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /rename <old_name> <new_name>")
        return
    old_name, new_name = context.args[0], " ".join(context.args[1:])
    session = sessions.find_one({"user_id": update.effective_user.id})
    if not session:
        await update.message.reply_text("⚠️ Please /login first.")
        return
    try:
        mega = Mega()
        m = mega.login(session["email"], session["password"])
        files = m.get_files()
        renamed = False
        for fid, fdata in files.items():
            if isinstance(fdata, dict) and "a" in fdata and fdata["a"].get("n") == old_name:
                m.rename(fid, new_name)
                renamed = True
                break
        if renamed:
            await update.message.reply_text(f"✅ Renamed {old_name} → {new_name}")
        else:
            await update.message.reply_text("❌ File not found.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sessions.delete_one({"user_id": update.effective_user.id})
    await update.message.reply_text("✅ Logged out successfully!")

# Handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("login", login))
application.add_handler(CommandHandler("rename", rename))
application.add_handler(CommandHandler("logout", logout))

# Run
if __name__ == "__main__":
    # Run Flask on PORT
    def run_flask():
        port = int(os.getenv("PORT", 8080))
        app.run(host="0.0.0.0", port=port)
    threading.Thread(target=run_flask).start()

    # Run Telegram Bot
    application.run_polling()
