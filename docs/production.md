# BIBC Production Deployment Guide

## 1. Environment Configuration

BIBC reads configuration from environment variables or a local `.env` file via `python-dotenv`.

| Variable | Required | Default | Description |
|---|---|---|---|
| `DISCORD_TOKEN` | Yes | None | Discord Bot token from Developer Portal |
| `DATABASE_PATH` | No | `./data/bibc.db` | Path to SQLite database file |

Never commit `.env` into version control. Ensure `.env` is listed in `.gitignore`.

## 2. Database Persistence & Backup

BIBC uses SQLite for persistent storage of server configurations and moderation records.

- Database location: `./data/bibc.db` (or custom path via `DATABASE_PATH`).
- State managed:
  - `guild_configs`: per-guild watch channel, execution policy, report channel.
  - `ban_records`: persistent moderation history and detection logs.
- Backup:
  Create a copy of `./data/bibc.db` before performing bot updates or host migrations.
  ```bash
  cp ./data/bibc.db ./data/bibc.db.bak.$(date +%Y%m%d%H%M%S)
  ```

## 3. Slash Commands

### `/config watchchannel <channel>`
- Permissions: Administrator only, Guild only.
- Description: Configures the designated honeypot channel for the current server.

### `/config policy <enforced|permissive>`
- Permissions: Administrator only, Guild only.
- Description: Sets policy to `enforced` (automatic ban with 5-minute message deletion) or `permissive` (detection and logging only, no ban).

### `/status`
- Permissions: Everyone.
- Description: Displays bot operational information, uptime, server policy, and persistent ban statistics (Total / Month / Week).

## 4. Policy Semantics

- `enforced`: When a message is detected in the watch channel, BIBC immediately bans the offending user with reason `gửi tin nhắn vào kênh lọc spam` and deletes the past 300 seconds of their messages. The event is recorded in the database with status `banned` and reported to the report channel if configured.
- `permissive`: When a message is detected, no moderation ban is issued. The event is recorded in the database with status `detected` and reported to the report channel.

## 5. Production Launch Sequence

```bash
# 1. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and enter your DISCORD_TOKEN

# 4. Start the bot
python bot.py
```

## 6. Migration from Legacy Versions (v2.0 Pre-Refactor)

- Global in-code variables `botToken`, `ChID`, `reportChID`, and `isLogOnlyMode` are deprecated and no longer read.
- Server configuration is now stored per-guild in SQLite.
- Run `/config watchchannel <channel>` and `/config policy <enforced|permissive>` in each server to initialize guild configuration.
