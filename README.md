# BanInBlacklistedChannels 2.0 (Production Refactor)

BanInBlacklistedChannels (BIBC) is a dedicated honeypot spam prevention bot for Discord servers.

## Features

- **Honeypot channel monitoring**: Automatically intercepts messages sent into blacklisted channels.
- **Persistent Per-Guild Configuration**: Database-backed channel configuration and policy per server.
- **Execution Policies**:
  - `enforced`: Immediate member ban with 5-minute message deletion window.
  - `permissive`: Event logging and database auditing without banning.
- **Audit & Statistics**: Tracks total, monthly, and weekly moderation actions in SQLite.
- **Resilient Lifecycle**: Graceful shutdown, isolated reporting, and bounded duplicate message protection.

## Getting Started

### Prerequisites

- Python 3.10+ (Recommended: Python 3.13+)
- Discord Bot Token with Server Members and Message Content intents enabled.

### Installation

```bash
# Clone repository
git clone https://github.com/MeowIce/bibc.git
cd bibc

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and supply DISCORD_TOKEN
```

### Running the Bot

```bash
python bot.py
```

## Slash Commands

- `/config watchchannel <channel>`: Set the monitored honeypot channel (Admin only, server only).
- `/config reportchannel <channel>`: Set the event report channel for embed logs (Admin only, server only).
- `/config policy <enforced|permissive>`: Switch policy between enforced and permissive (Admin only, server only).
- `/status`: View bot status, uptime, server policy, and persistent ban statistics.

For full deployment and architecture details, see [docs/production.md](docs/production.md).

## License

Copyright (c) 2026 MeowIce

Permission is granted to use, modify, and distribute this software for non-commercial purposes only.
Selling this software or any derivative works is prohibited without explicit written permission.
Removing or altering author credits is prohibited.
