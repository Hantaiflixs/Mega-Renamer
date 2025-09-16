# MEGA Rename Bot (Telegram)

Simple Telegram bot that logs into MEGA (in-memory), renames all files/folders to a base name, and logs out.

## Features
- /login -> login to MEGA (kept in memory)
- /rename_all <basename> -> rename all files/folders to `<basename>_1`, `<basename>_2`, ...
- auto logout after rename
- works with large accounts (only renames metadata)

## Setup (local)
1. Clone:
   ```bash
   git clone <your-repo-url>
   cd mega-rename-bot
