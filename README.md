# Mega.nz Rename Bot

A Telegram bot to login into your Mega.nz account and rename files/folders.

## Features
- 🔑 Login with Mega.nz credentials
- ✏️ Rename files/folders
- 🚪 Logout anytime
- 🌐 MongoDB session storage
- ✅ Supports up to 200GB (Mega limits apply)

---

## Deploy Guide

### 🔹 Render
1. Fork this repo
2. Create **Web Service**
3. Add ENV variables:
   - `BOT_TOKEN` = Telegram Bot Token
   - `MONGO_URI` = MongoDB connection string
4. Build Command → `pip install -r requirements.txt`
5. Start Command → `gunicorn bot:app --bind 0.0.0.0:$PORT`
6. Deploy 🚀

---

### 🔹 Koyeb
1. Fork this repo
2. Create new **Service**
3. Runtime → Python
4. Add ENV:
   - `BOT_TOKEN`
   - `MONGO_URI`
5. Expose Port → `$PORT`
6. Deploy 🚀

---

### 🔹 Heroku
1. Install Heroku CLI
2. Run:
   ```bash
   heroku create mega-rename-bot
   heroku config:set BOT_TOKEN=your_token MONGO_URI=your_mongo_uri
   git push heroku main
