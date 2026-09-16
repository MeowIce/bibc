# BanInBlacklistedChannel Production Refactor Design

**Date:** 2026-09-13
**Status:** Approved

## Goal
Refactor BanInBlacklistedChannel (BIBC) into a production-oriented 24/7 Discord bot while preserving the core detection, ban, policy, and reporting behavior. Add persistent guild configuration and ban-event storage, weekly/monthly statistics, `/config`, renamed `/status`, environment-based secrets, and a production-safe status presence.

## Approved Architecture
Use SQLite as the persistent datastore, Python `logging` for structured application logging, `.env` for secrets/configuration, and a repository/service architecture around the existing `discord.py` bot. Database state is the source of truth for guild configuration and ban history; optional runtime caching must never replace persistence.

## Core Behavior
- `enforced`: a message in the configured watch channel causes a ban attempt, followed by event persistence and reporting.
- `permissive`: a message in the configured watch channel is recorded/reported but does not ban.
- Only guild configuration determines which channel is watched.
- `/config watchchannel <id>` and `/config policy <enforced|permissive>` are administrator-only and guild-only.
- `/info` is replaced by `/status`.
- Status text must be exactly shaped as `Status type: watching, [#] servers - [#] members`.

## Persistence
`guild_configs` stores guild-specific watch channel, policy, optional report channel configuration, and timestamps. `ban_records` stores guild/user/channel/message identifiers, username, policy, action, reason, and UTC event timestamp. Index guild IDs, event timestamps, and user IDs as appropriate for statistics and lookup.

## Security
Move the Discord token and database path out of source into `.env`; create `.env.example`; ignore `.env` and runtime database/data files in Git. Never log the token or other secrets.

## Reliability
Use narrow Discord exception handling, graceful shutdown, resilient reporting, transaction-aware database writes, UTC timestamps, duplicate-event protection, permission/hierarchy checks before ban attempts, and logging that does not dump unlimited message content. Database failures must be observable and must not crash the message watcher.

## Issues Identified in Existing Source
1. Token/config values are source-level configuration.
2. Watch/report channels are global rather than per guild.
3. `PolicyModes` is RAM-only and reset by `on_ready`.
4. `bannedUsers` is RAM-only.
5. Concurrent messages can trigger duplicate ban attempts.
6. Broad `except Exception` obscures operational failures.
7. `print()` is unsuitable as the application logging abstraction.
8. Full message content is written to logs without size control.
9. Slash-command sync is tied directly to every `on_ready` invocation.
10. Global/local variable shadowing makes state behavior harder to reason about.
11. DM/guild command boundaries are not consistently modeled.
12. Permission handling relies mainly on command metadata.
13. Ban and report operations are coupled in one event handler.
14. Ban permission and role-hierarchy failures are not explicitly classified.
15. There is no explicit graceful database/resource shutdown.

## Non-Goals
Do not add unrelated commands, a web dashboard, PostgreSQL/MySQL, distributed locking, external metrics infrastructure, or a major rewrite of Discord functionality beyond the approved requirements.
