# BanInBlacklistedChannel Production Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor BIBC into a stable 24/7 production bot with persistent SQLite configuration/statistics, secure environment configuration, `/config`, `/status`, resilient moderation/reporting, and preserved core behavior.

**Architecture:** Keep `discord.py` as the Discord runtime, but split configuration, database access, repositories, services, cogs/commands, and message watching into focused modules. SQLite is the persistent source of truth; services coordinate business behavior; repositories contain SQL; Discord handlers remain thin.

**Tech Stack:** Python 3.x, `discord.py`, SQLite via the Python standard-library `sqlite3` module, `python-dotenv`, `pytest`, `pytest-asyncio`.

**Spec:** `docs/superpowers/specs/2026-09-13-bibc-production-refactor-design.md`

## Global Constraints

- Preserve the existing core behavior of watching configured channels, enforcing a ban in enforced mode, reporting events, and allowing permissive/log-only operation.
- Replace global channel configuration with per-guild database configuration.
- Policy values are exactly `enforced` and `permissive`.
- `/config watchchannel <id>` and `/config policy <enforced|permissive>` are administrator-only and guild-only.
- Rename `/info` to `/status`.
- Status format is exactly `Status type: watching, [#] servers - [#] members`.
- Use UTC for persisted event timestamps and time-window calculations.
- Secrets must not be stored in source code; use `.env` and provide `.env.example`.
- `.env` and runtime database/data files must not be committed.
- SQLite is the only database required by this plan.
- Database state is the source of truth; runtime caches are optional optimizations only.
- Production errors must be logged with `logging`, not raw `print()` calls.
- Never log the Discord bot token or other secrets.
- Do not introduce unrelated features or change the moderation policy semantics beyond the approved `enforced`/`permissive` behavior.

---

## File Map

The implementation should converge on this structure:

```text
.
├── bot.py
├── config.py
├── database.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── cogs/
│   ├── config.py
│   └── status.py
├── models/
│   ├── guildConfig.py
│   └── banRecord.py
├── repositories/
│   ├── guildConfigRepository.py
│   └── banRepository.py
├── services/
│   ├── guildConfigService.py
│   ├── banService.py
│   ├── reportService.py
│   └── statisticsService.py
├── utils/
│   ├── logging.py
│   └── time.py
└── tests/
    ├── conftest.py
    ├── testConfig.py
    ├── testDatabase.py
    ├── testGuildConfigRepository.py
    ├── testBanRepository.py
    ├── testGuildConfigService.py
    ├── testBanService.py
    ├── testStatisticsService.py
    ├── testConfigCog.py
    ├── testStatusCog.py
    └── testMessageWatcher.py
```

If the existing repository uses a different package root, preserve the same responsibility boundaries while adapting paths. Do not create unnecessary compatibility wrappers once imports have been migrated.

---

### Task 1: Capture Existing Behavior With Regression Tests

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/testMessageWatcher.py`
- Create: `tests/testConfigCog.py`
- Create: `tests/testStatusCog.py`
- Modify: existing bot module only as needed to make behavior testable without changing behavior

**Interfaces:**
- Consumes: current BIBC behavior in `opensrc.py`, including message filtering, policy handling, ban invocation, reporting, and command behavior.
- Produces: regression coverage that later refactors must keep passing.

- [x] **Step 1: Add the test dependencies and test configuration.**

Add `pytest` and `pytest-asyncio` to the development/test dependency set. Configure async tests with the repository's supported pytest-asyncio mode rather than relying on implicit event-loop behavior.

- [x] **Step 2: Write a failing test for watched-channel detection.**

Construct a minimal fake Discord message with a guild, channel, author, and content. Assert that a message whose channel matches the configured watched channel reaches the moderation path and an unrelated channel does not.

- [x] **Step 3: Write a failing test for enforced behavior.**

Mock the guild ban operation. Send a watched-channel message under enforced policy and assert that the author is passed to the ban operation with the configured reason and five-minute message deletion window.

- [x] **Step 4: Write a failing test for permissive behavior.**

Send the same message under permissive policy and assert that no ban call occurs while the event remains eligible for reporting/recording.

- [x] **Step 5: Write a failing test for bot-user exclusion and DM exclusion.**

Assert that the bot does not moderate its own messages and that a DM never enters guild moderation logic.

- [x] **Step 6: Write a failing test for `/status` output semantics.**

Mock the bot guild collection and member counts and assert the final text matches `Status type: watching, [#] servers - [#] members`.

- [x] **Step 7: Run the focused tests and record the baseline failures.**

Run:

```bash
pytest tests/testMessageWatcher.py tests/testConfigCog.py tests/testStatusCog.py -v
```

Expected: the newly introduced tests expose current architectural gaps but do not alter production behavior yet.

- [x] **Step 8: Commit the regression-test baseline.**

```bash
git add tests
 git commit -m "test: capture BIBC behavior before production refactor"
```

---

### Task 2: Introduce Secure Environment Configuration and Logging

**Files:**
- Create: `config.py`
- Create: `utils/logging.py`
- Create: `.env.example`
- Modify: `.gitignore`
- Modify: `requirements.txt`
- Modify: `bot.py`
- Test: `tests/testConfig.py`

**Interfaces:**
- Consumes: `.env` values through `python-dotenv`.
- Produces: `AppConfig` with `discordToken` and `databasePath`; `configureLogging()` for application logging.

- [x] **Step 1: Write failing configuration tests.**

Test that a populated environment produces the expected token and database path, and that a missing `DISCORD_TOKEN` raises a clear configuration error before attempting to connect to Discord.

- [x] **Step 2: Run the configuration tests to verify failure.**

```bash
pytest tests/testConfig.py -v
```

Expected: FAIL because the new configuration module does not yet exist.

- [x] **Step 3: Implement `AppConfig` loading.**

Define a small immutable configuration object or dataclass with:

```text
loadConfig() -> AppConfig
AppConfig.discordToken: str
AppConfig.databasePath: str
```

Load `.env` before reading variables. Use `DATABASE_PATH=./data/bibc.db` as the example default/documented value. Do not provide a fallback token.

- [x] **Step 4: Implement production logging.**

Create `configureLogging()` using Python's `logging` module with UTC-aware timestamps and a stable format containing level, logger name, and message. Do not log secrets. Provide module-level loggers with `logging.getLogger(__name__)` in consuming modules.

- [x] **Step 5: Create `.env.example`.**

Use:

```dotenv
DISCORD_TOKEN=your_discord_bot_token
DATABASE_PATH=./data/bibc.db
```

Do not place a real token in this file.

- [x] **Step 6: Update `.gitignore`.**

Ignore:

```text
.env
.env.*.local
data/
__pycache__/
*.pyc
.pytest_cache/
```

Do not ignore `.env.example`.

- [x] **Step 7: Update `requirements.txt`.**

Add `python-dotenv` as a runtime dependency and `pytest`/`pytest-asyncio` as test dependencies if the repository maintains a single requirements file. Preserve the currently supported `discord.py` dependency/version unless the existing project explicitly pins another version.

- [x] **Step 8: Replace the hard-coded token/config in `bot.py`.**

Load `AppConfig` once during process startup and pass the resulting configuration into components that need it. Remove `botToken`, `ChID`, `reportChID`, `actionReason`, and `isLogOnlyMode` global configuration constants from the source.

- [x] **Step 9: Run tests.**

```bash
pytest tests/testConfig.py -v
```

Expected: PASS.

- [x] **Step 10: Commit.**

```bash
git add config.py utils/logging.py .env.example .gitignore requirements.txt bot.py tests/testConfig.py
git commit -m "refactor: move BIBC configuration to environment"
```

---

### Task 3: Build the SQLite Database Layer and Schema

**Files:**
- Create: `database.py`
- Create: `models/guildConfig.py`
- Create: `models/banRecord.py`
- Create: `tests/testDatabase.py`

**Interfaces:**
- Consumes: `AppConfig.databasePath`.
- Produces: `Database` connection/lifecycle abstraction and schema initialization for `guild_configs` and `ban_records`.

- [x] **Step 1: Write failing schema tests.**

Use a temporary SQLite path. Assert that initialization creates both tables and the required indexes, and that calling initialization twice is safe.

- [x] **Step 2: Run the schema tests.**

```bash
pytest tests/testDatabase.py -v
```

Expected: FAIL because the database layer does not exist.

- [x] **Step 3: Define the `GuildConfig` model.**

Represent:

```text
guildId: int
watchChannelId: int | None
policy: str
reportChannelId: int | None
createdAt: datetime
updatedAt: datetime
```

Policy must be validated to exactly `enforced` or `permissive`.

- [x] **Step 4: Define the `BanRecord` model.**

Represent:

```text
id: int | None
guildId: int
userId: int
username: str
channelId: int
messageId: int
policy: str
action: str
reason: str
createdAt: datetime
```

Use UTC timestamps and preserve Discord snowflake IDs as integers.

- [x] **Step 5: Implement database connection management.**

Create a `Database` class with:

```text
__init__(path: str)
connect() -> sqlite3.Connection
initialize() -> None
close() -> None
```

Configure SQLite for a long-running single-process bot with foreign keys enabled and a sensible busy timeout. Keep transactions explicit around writes.

- [x] **Step 6: Create the `guild_configs` schema.**

Use `guild_id` as the primary key. Store watch channel, policy, optional report channel, and UTC creation/update timestamps. Add a constraint that policy can only contain `enforced` or `permissive`.

- [x] **Step 7: Create the `ban_records` schema.**

Store each moderation/detection event. Add indexes on `(guild_id, created_at)`, `created_at`, and `(guild_id, user_id)` for guild/time/user queries.

- [x] **Step 8: Implement safe UTC serialization.**

Persist ISO-8601 UTC strings consistently or use integer epoch seconds consistently. Pick one representation and use it everywhere. The implementation must parse it back without local-time ambiguity.

- [x] **Step 9: Run schema tests.**

```bash
pytest tests/testDatabase.py -v
```

Expected: PASS.

- [x] **Step 10: Commit.**

```bash
git add database.py models tests/testDatabase.py
 git commit -m "feat: add SQLite persistence layer"
```

---

### Task 4: Implement Guild Configuration Repository and Service

**Files:**
- Create: `repositories/guildConfigRepository.py`
- Create: `services/guildConfigService.py`
- Create: `tests/testGuildConfigRepository.py`
- Create: `tests/testGuildConfigService.py`

**Interfaces:**
- Consumes: `Database`, `GuildConfig`.
- Produces:
  - `GuildConfigRepository.get(guildId) -> GuildConfig | None`
  - `GuildConfigRepository.upsertWatchChannel(guildId, channelId) -> GuildConfig`
  - `GuildConfigRepository.updatePolicy(guildId, policy) -> GuildConfig`
  - `GuildConfigService.getConfig(guildId) -> GuildConfig | None`
  - `GuildConfigService.setWatchChannel(guildId, channelId) -> GuildConfig`
  - `GuildConfigService.setPolicy(guildId, policy) -> GuildConfig`

- [x] **Step 1: Write repository tests for missing configuration.**

Assert `get(guildId)` returns `None` when no row exists.

- [x] **Step 2: Write repository tests for watch-channel persistence.**

Insert a guild configuration, read it back, update the channel, read it again, and assert timestamps/configuration survive a new database connection.

- [x] **Step 3: Write repository tests for policy persistence.**

Assert both allowed policies persist and an invalid policy is rejected before SQL execution.

- [x] **Step 4: Run repository tests and verify failure.**

```bash
pytest tests/testGuildConfigRepository.py -v
```

Expected: FAIL until the repository is implemented.

- [x] **Step 5: Implement repository SQL with parameterized queries.**

Never interpolate guild/channel IDs or policy strings directly into SQL. Use SQLite parameters for every value.

- [x] **Step 6: Write service tests for business validation.**

Test that a negative/invalid channel ID is rejected, guild IDs are required, and policy values outside `enforced`/`permissive` are rejected.

- [x] **Step 7: Implement `GuildConfigService`.**

Keep business validation in the service/model boundary and persistence details in the repository. Do not maintain a second authoritative `PolicyModes` dictionary.

- [x] **Step 8: Run service and repository tests.**

```bash
pytest tests/testGuildConfigRepository.py tests/testGuildConfigService.py -v
```

Expected: PASS.

- [x] **Step 9: Commit.**

```bash
git add repositories/guildConfigRepository.py services/guildConfigService.py tests/testGuildConfigRepository.py tests/testGuildConfigService.py
git commit -m "feat: add persistent per-guild configuration"
```

---

### Task 5: Implement Ban Repository and Statistics Queries

**Files:**
- Create: `repositories/banRepository.py`
- Create: `services/statisticsService.py`
- Create: `utils/time.py`
- Create: `tests/testBanRepository.py`
- Create: `tests/testStatisticsService.py`

**Interfaces:**
- Consumes: `Database`, `BanRecord`.
- Produces:
  - `BanRepository.insert(record) -> BanRecord`
  - `BanRepository.countSince(startTime, guildId=None) -> int`
  - `BanRepository.countUniqueUsersSince(startTime, guildId=None) -> int`
  - `StatisticsService.countThisWeek(guildId=None) -> int`
  - `StatisticsService.countThisMonth(guildId=None) -> int`
  - `StatisticsService.countTotal(guildId=None) -> int`

- [x] **Step 1: Define the event semantics before implementation.**

Use `action` to distinguish at minimum `banned` from `detected`/`failed` so statistics can count actual successful bans rather than all detections. Weekly/monthly ban statistics must count records whose action represents a successful ban.

- [x] **Step 2: Write failing tests for insert and retrieval counts.**

Insert records for multiple guilds, users, and timestamps. Assert guild filtering and time filtering work independently.

- [x] **Step 3: Write failing tests for week/month boundaries.**

Use fixed UTC datetimes rather than `datetime.now()` in tests. Verify events exactly at the start boundary are included and events immediately before it are excluded.

- [x] **Step 4: Run tests to verify failure.**

```bash
pytest tests/testBanRepository.py tests/testStatisticsService.py -v
```

Expected: FAIL until repository/service implementation exists.

- [x] **Step 5: Implement `BanRepository.insert`.**

Use a transaction and return the stored record with its generated ID. Roll back on SQLite errors and propagate a typed repository/database exception after logging at the caller boundary.

- [x] **Step 6: Implement time-window helpers.**

Define deterministic helpers such as:

```text
utcNow() -> datetime
startOfUtcWeek(now) -> datetime
startOfUtcMonth(now) -> datetime
```

Use Monday as the start of the UTC week and the first calendar day as the start of the UTC month. Keep these calculations isolated in `utils/time.py` so they can be tested without Discord.

- [x] **Step 7: Implement statistics service.**

Count only successful bans for weekly/monthly/total ban statistics. Use SQL `COUNT(*)` rather than loading all records into Python.

- [x] **Step 8: Test persistence across connections.**

Insert records, close the database, reopen it, and verify statistics remain available.

- [x] **Step 9: Run tests.**

```bash
pytest tests/testBanRepository.py tests/testStatisticsService.py -v
```

Expected: PASS.

- [x] **Step 10: Commit.**

```bash
git add repositories/banRepository.py services/statisticsService.py utils/time.py tests/testBanRepository.py tests/testStatisticsService.py
git commit -m "feat: persist ban events and add time statistics"
```

---

### Task 6: Refactor Ban and Reporting Into Services

**Files:**
- Create: `services/banService.py`
- Create: `services/reportService.py`
- Modify: `bot.py` or the eventual watcher module
- Test: `tests/testBanService.py`

**Interfaces:**
- Consumes: Discord guild/member/message objects, `GuildConfigService`, `BanRepository`, and `ReportService`.
- Produces:
  - `BanService.handleMessage(message, guildConfig) -> BanResult`
  - `ReportService.sendEventReport(guild, message, action, reason) -> None`

`BanResult` should carry a stable action value such as `banned`, `detected`, or `failed` and a human-readable reason suitable for reporting.

- [x] **Step 1: Write failing tests for successful enforced bans.**

Mock the Discord guild ban method and assert:

```text
reason == configured action reason
 delete_message_seconds == 300
```

and the result action is `banned`.

- [x] **Step 2: Write failing tests for permissive mode.**

Assert no Discord ban call occurs and the result action is `detected`.

- [x] **Step 3: Write failing tests for Discord permission failures.**

Mock `discord.Forbidden` and assert the service returns `failed` without raising an exception into the message event loop.

- [x] **Step 4: Write failing tests for target hierarchy/not-found/HTTP errors.**

Mock the corresponding Discord exceptions available in the installed `discord.py` version and assert each becomes a controlled failure with an actionable log message.

- [x] **Step 5: Run service tests to verify failure.**

```bash
pytest tests/testBanService.py -v
```

Expected: FAIL until the service exists.

- [x] **Step 6: Implement explicit ban eligibility checks.**

Before calling `guild.ban`, check the bot's guild permissions and target hierarchy where Discord.py exposes the relevant properties. Treat owner/administrator/hierarchy/permission failures as non-ban outcomes rather than generic crashes.

- [x] **Step 7: Implement `BanService.handleMessage`.**

The service must:

1. receive already-filtered watched-channel messages;
2. skip the ban operation for permissive policy;
3. attempt exactly one ban for enforced policy;
4. return a stable result;
5. never catch `BaseException` or suppress process-control exceptions.

- [x] **Step 8: Implement `ReportService`.**

Resolve the report channel from guild configuration rather than a global list. If no report channel is configured, skip reporting with an informational log. If sending fails, log the failure without changing the moderation result.

Truncate message content before embedding it so a pathological message cannot exceed Discord embed/message limits. Escape/format content safely as plain text rather than treating it as arbitrary Markdown structure.

- [x] **Step 9: Persist the moderation event after the service result is known.**

Record the event using `BanRepository`. For a successful ban use `action=banned`; for permissive use `action=detected`; for an unsuccessful ban use `action=failed`. Preserve the original message ID and channel ID for auditability.

- [x] **Step 10: Run service tests.**

```bash
pytest tests/testBanService.py -v
```

Expected: PASS.

- [x] **Step 11: Commit.**

```bash
git add services/banService.py services/reportService.py bot.py tests/testBanService.py
git commit -m "refactor: isolate moderation and reporting services"
```

---

### Task 7: Implement the Message Watcher and Remove RAM-Only Policy State

**Files:**
- Create or extract: `messageWatcher.py` if needed
- Modify: `bot.py`
- Modify: `tests/testMessageWatcher.py`

**Interfaces:**
- Consumes: `GuildConfigService`, `BanService`, `BanRepository`, `ReportService`.
- Produces: one production `on_message` path that uses persisted guild configuration.

- [x] **Step 1: Add a failing persistence/restart test.**

Set a guild's watch channel and policy through the service, construct a fresh watcher with a new database connection, and assert it retrieves the same configuration without relying on an in-memory dictionary.

- [x] **Step 2: Add a failing test for no configuration.**

Assert a guild without a `guild_configs` row is ignored without a ban and without an error.

- [x] **Step 3: Add a failing test for duplicate rapid messages.**

Deliver two messages from the same author to the same watched channel in rapid succession and verify the implementation does not intentionally issue duplicate bans for the same moderation event. Use the message ID as the primary event identity and do not globally suppress legitimate distinct messages.

- [x] **Step 4: Implement the watcher.**

The watcher should execute:

```text
ignore bot author
→ ignore DM
→ load guild config
→ ignore missing config
→ ignore non-watched channel
→ call BanService
→ persist result
→ report independently
→ process commands
```

Do not use `ChID`, `PolicyModes`, `bannedUsers`, or a global `isLogOnlyMode`.

- [x] **Step 5: Add an in-process event guard only where required.**

Use a bounded set/cache keyed by `(guildId, messageId)` to prevent accidental duplicate handling of the exact same Discord message. Do not use an unbounded list of users, because the old `bannedUsers` list is a memory-growth risk and would incorrectly suppress future independent messages.

- [x] **Step 6: Ensure command processing remains functional.**

Call `bot.process_commands(message)` exactly once for non-ignored messages and ensure the watcher does not prevent unrelated prefix-command processing if such commands remain enabled.

- [x] **Step 7: Run watcher regression tests.**

```bash
pytest tests/testMessageWatcher.py -v
```

Expected: PASS.

- [x] **Step 8: Run the full current test suite.**

```bash
pytest -v
```

Expected: PASS.

- [x] **Step 9: Commit.**

```bash
git add bot.py messageWatcher.py tests/testMessageWatcher.py
 git commit -m "refactor: use persistent guild configuration in watcher"
```

---

### Task 8: Replace Legacy Commands With `/config`

**Files:**
- Create: `cogs/config.py`
- Modify: `bot.py`
- Test: `tests/testConfigCog.py`

**Interfaces:**
- Consumes: `GuildConfigService` and Discord `Interaction`.
- Produces:
  - `/config watchchannel <id>`
  - `/config policy <enforced|permissive>`

- [x] **Step 1: Write failing command tests.**

Test that a non-guild interaction is rejected, a non-administrator is rejected, and an administrator in a guild can update configuration.

- [x] **Step 2: Write failing validation tests for channel IDs.**

Given an ID that does not resolve to a channel in the current guild, assert the command returns a clear failure and does not write invalid configuration.

- [x] **Step 3: Write failing tests for policy choices.**

Assert only `enforced` and `permissive` can reach the service. Prefer Discord autocomplete/choices so invalid values are prevented at the UI level as well as validated server-side.

- [x] **Step 4: Implement `/config` as a slash-command group.**

Use a command group named `config` with the two subcommands. Both must be guild-only and administrator-only. Do not trust only client-side command metadata; check `interaction.guild`, `interaction.user.guild_permissions.administrator`, and required channel ownership/existence in the guild before changing state.

- [x] **Step 5: Implement watch-channel validation.**

Resolve the channel ID through the current guild's channel collection/cache or fetch when necessary. Ensure the resolved channel belongs to the current guild. Reject unsupported channel types if the watcher cannot observe them reliably as Discord messages.

- [x] **Step 6: Implement policy persistence.**

Write through `GuildConfigService.setPolicy`. Return a concise confirmation showing the stored value.

- [x] **Step 7: Remove `/epedit` and `/getpolicy`.**

Do not retain duplicate legacy configuration commands unless the existing project has an explicit compatibility requirement not present in this spec. The new `/config` commands are the canonical interface.

- [x] **Step 8: Run command tests.**

```bash
pytest tests/testConfigCog.py -v
```

Expected: PASS.

- [x] **Step 9: Commit.**

```bash
git add cogs/config.py bot.py tests/testConfigCog.py
 git commit -m "feat: add per-guild config slash commands"
```

---

### Task 9: Replace `/info` With `/status` and Implement Status Presence

**Files:**
- Create: `cogs/status.py`
- Modify: `bot.py`
- Test: `tests/testStatusCog.py`

**Interfaces:**
- Consumes: Discord bot state and `StatisticsService` where status statistics are displayed.
- Produces: `/status` and a presence/activity string with exact format `Status type: watching, [#] servers - [#] members`.

- [x] **Step 1: Write failing `/status` tests.**

Assert the command exists as `/status`, not `/info`, and that it returns a Discord embed containing the bot ID, uptime, current guild policy when applicable, and persistent ban statistics where those fields remain useful. Do not preserve obsolete `/info` naming.

- [x] **Step 2: Write failing tests for server/member counting.**

Construct fake guilds with overlapping members and verify the implementation uses unique account IDs rather than blindly summing duplicate member objects. If the bot only has partial member caches, use the counts available from Discord guild objects and document the chosen semantics in code.

- [x] **Step 3: Implement `/status`.**

Retain useful operational information from `/info`, but rename the command and remove the runtime-only `bannedUsers` statistic. Use `StatisticsService` for persistent ban counts.

- [x] **Step 4: Implement the exact status activity string.**

Build:

```text
Status type: watching, {serverCount} servers - {memberCount} members
```

Do not add Markdown, backticks, punctuation, or extra labels to the activity string.

- [x] **Step 5: Update presence at startup and on guild membership changes.**

Create a small helper such as `updateBotStatus()` and invoke it after `on_ready`, `on_guild_join`, and `on_guild_remove`. Avoid a tight periodic task unless Discord state freshness requires it.

- [x] **Step 6: Remove `/info`.**

Do not register both commands. The requested interface is `/status`.

- [x] **Step 7: Run status tests.**

```bash
pytest tests/testStatusCog.py -v
```

Expected: PASS.

- [x] **Step 8: Commit.**

```bash
git add cogs/status.py bot.py tests/testStatusCog.py
 git commit -m "feat: replace info with status and bot presence"
```

---

### Task 10: Harden Startup, Reconnect, Shutdown, and Command Synchronization

**Files:**
- Modify: `bot.py`
- Modify: `database.py`
- Modify: `utils/logging.py`
- Create/modify: `tests/testDatabase.py`

**Interfaces:**
- Consumes: all services/cogs.
- Produces: a lifecycle-safe application that initializes database state once, loads extensions deterministically, synchronizes commands without destructive repeated work, and closes database resources on shutdown.

- [x] **Step 1: Write lifecycle tests.**

Test database initialization occurs once, shutdown closes the connection, and repeated readiness events do not recreate conflicting resources.

- [x] **Step 2: Move application setup out of import-time side effects.**

Avoid connecting to Discord or performing database writes merely by importing `bot.py`. Create explicit setup functions/classes where practical.

- [x] **Step 3: Initialize the database before registering event handlers that need it.**

Call `Database.initialize()` before the bot begins handling guild messages.

- [x] **Step 4: Load cogs exactly once.**

Use the standard extension-loading lifecycle supported by the installed `discord.py` version. Avoid repeatedly adding the same cog after reconnect.

- [x] **Step 5: Handle command synchronization deliberately.**

Do not perform an unconditional `bot.tree.sync()` on every reconnect through `on_ready`. Place sync in the startup lifecycle where it runs once per process start, or use the project's chosen scoped-sync strategy if guild-specific development sync is required.

- [x] **Step 6: Add graceful shutdown.**

Ensure database close and bot close happen in a `finally`/shutdown lifecycle path. Do not catch `KeyboardInterrupt`/`SystemExit` as ordinary errors.

- [x] **Step 7: Add startup diagnostics without secrets.**

Log bot version, guild count, database path, and configured component readiness. Never log `DISCORD_TOKEN`.

- [x] **Step 8: Run lifecycle tests and full tests.**

```bash
pytest -v
```

Expected: PASS.

- [x] **Step 9: Commit.**

```bash
git add bot.py database.py utils/logging.py tests
git commit -m "refactor: harden BIBC application lifecycle"
```

---

### Task 11: Production Error Handling, Logging, and Resource Hardening

**Files:**
- Modify: `bot.py`
- Modify: `messageWatcher.py`
- Modify: `services/banService.py`
- Modify: `services/reportService.py`
- Modify: `repositories/*.py`
- Modify: `utils/logging.py`
- Add/modify: relevant tests

**Interfaces:**
- Consumes: all previous service/repository interfaces.
- Produces: predictable operational failure handling and bounded resource usage.

- [x] **Step 1: Replace remaining `print()` calls.**

Search:

```bash
grep -R "print(" -n . --exclude-dir=.git --exclude-dir=.venv
```

Replace application diagnostics with named loggers and appropriate levels.

- [x] **Step 2: Remove broad `except Exception` from business logic.**

Search:

```bash
grep -R "except Exception" -n . --exclude-dir=.git --exclude-dir=.venv
```

Replace with explicit exceptions where the failure is expected. At top-level event boundaries, a final `except Exception` may remain only to log unexpected errors and prevent a single event from terminating the event task; it must use `logger.exception()` and must not swallow process-control exceptions.

- [x] **Step 3: Bound logged message content.**

Create a single helper for truncating content to a safe logging/reporting size. Logs should contain message metadata by default. Report embeds may include bounded content because it is part of the moderation report.

- [x] **Step 4: Make reporting failure-isolated.**

A report-channel failure must not convert a successful ban into a failed moderation action. Log report failures separately.

- [x] **Step 5: Make database writes transaction-safe.**

Every insert/update must commit on success and roll back on database failure. Ensure cursors/connections are closed or managed with context managers.

- [x] **Step 6: Add explicit operational logs for ban failures.**

Include guild ID, user ID, channel ID, message ID, action, and Discord exception class. Do not include secrets and do not dump arbitrary exception objects if they can contain sensitive request data.

- [x] **Step 7: Verify no unbounded runtime lists remain.**

Search for append-only collections used to track events. Ban history must live in SQLite. Any duplicate-event cache must have bounded size/TTL.

- [x] **Step 8: Run the full suite.**

```bash
pytest -v
```

Expected: PASS.

- [x] **Step 9: Commit.**

```bash
git add .
git commit -m "fix: harden BIBC production error handling"
```

---

### Task 12: Add Integration Tests for the Full Moderation Pipeline

**Files:**
- Create: `tests/testIntegration.py`
- Modify: `tests/conftest.py`

**Interfaces:**
- Consumes: real temporary SQLite database plus mocked Discord objects.
- Produces: end-to-end confidence across configuration → watcher → ban service → database → report service.

- [x] **Step 1: Write enforced integration test.**

Create a temporary database, configure a guild with a watch channel and `enforced`, deliver a fake watched message, mock a successful ban, and assert:

```text
ban called once
ban_records contains action=banned
statistics count is 1
report attempted independently
```

- [x] **Step 2: Write permissive integration test.**

Assert:

```text
ban not called
ban_records contains action=detected
successful-ban statistics remains 0
report attempted
```

- [x] **Step 3: Write restart persistence integration test.**

Close the first database object, open a second one using the same path, and assert guild configuration and ban history remain intact.

- [x] **Step 4: Write missing-config integration test.**

Assert a message from an unconfigured guild causes no ban, no invalid database record, and no exception.

- [x] **Step 5: Write permission-failure integration test.**

Assert a Discord ban failure creates a `failed` event and does not increment successful-ban statistics.

- [x] **Step 6: Run integration tests.**

```bash
pytest tests/testIntegration.py -v
```

Expected: PASS.

- [x] **Step 7: Commit.**

```bash
git add tests/testIntegration.py tests/conftest.py
git commit -m "test: cover BIBC production moderation pipeline"
```

---

### Task 13: Documentation, Migration, and Production Configuration

**Files:**
- Modify: `README.md`
- Create: `docs/production.md`
- Modify: `.env.example`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: final implementation behavior.
- Produces: deployable, documented production configuration.

- [x] **Step 1: Document environment variables.**

Document every supported variable and explicitly state that `.env` must never be committed.

- [x] **Step 2: Document SQLite location and backup.**

Document that the database path is persistent state and should be backed up before upgrades or migrations.

- [x] **Step 3: Document the new commands.**

Include exact usage:

```text
/config watchchannel <id>
/config policy enforced
/config policy permissive
/status
```

State that `/config` requires Administrator permission and must be run inside a guild.

- [x] **Step 4: Document policy semantics.**

Explain exactly what `enforced` and `permissive` do and that detections remain persistent in permissive mode.

- [x] **Step 5: Document the report-channel configuration behavior.**

If the current implementation retains report-channel configuration, document its database-backed source and how it is initialized/migrated. Do not invent a new user-facing command unless it is required by the final repository state.

- [x] **Step 6: Document production launch.**

Provide a launch sequence that creates the virtual environment, installs dependencies, creates `.env` from `.env.example`, initializes the data directory, and starts the bot. Do not include a real token.

- [x] **Step 7: Document migration from the old runtime configuration.**

Explain that old global `ChID`, `reportChID`, and policy settings are no longer authoritative. If a migration utility is needed because production has existing channel IDs, implement a one-time explicit migration rather than silently guessing guild ownership.

- [x] **Step 8: Commit documentation.**

```bash
git add README.md docs/production.md .env.example .gitignore
git commit -m "docs: document BIBC production deployment"
```

---

### Task 14: Final Security, Compatibility, and Quality Review

**Files:**
- All project files

**Interfaces:**
- Consumes: complete implementation.
- Produces: verified release candidate with no known requirement gaps.

- [x] **Step 1: Run the complete test suite.**

```bash
pytest -v
```

Expected: all tests PASS.

- [x] **Step 2: Run syntax/import validation.**

```bash
python -m compileall .
```

Expected: no syntax errors.

- [x] **Step 3: Search for leaked secrets and legacy globals.**

```bash
grep -R "botToken\|ChID\|reportChID\|PolicyModes\|bannedUsers\|isLogOnlyMode" -n . --exclude-dir=.git --exclude-dir=.venv --exclude='.env.example'
```

Expected: no production source references to the removed authoritative globals.

- [x] **Step 4: Search for unsafe logging.**

```bash
grep -R "print(\|message.content" -n . --exclude-dir=.git --exclude-dir=.venv
```

Expected: no uncontrolled production `print()` diagnostics and no unbounded message-content logging.

- [x] **Step 5: Search for broad exception handling.**

```bash
grep -R "except Exception" -n . --exclude-dir=.git --exclude-dir=.venv
```

Expected: only deliberate top-level event boundaries remain, each using structured exception logging and preserving process-control behavior.

- [x] **Step 6: Verify `.env` handling.**

```bash
git status --short
```

Expected: `.env` and `data/` are ignored; `.env.example` is tracked.

- [x] **Step 7: Verify command names.**

Search source and command tree for `info`, `epedit`, and `getpolicy`. Expected canonical commands are `/config` and `/status`; no obsolete command registration remains.

- [x] **Step 8: Verify exact status presence string.**

Run the status formatting test and assert the literal template:

```text
Status type: watching, {serverCount} servers - {memberCount} members
```

- [x] **Step 9: Perform a manual Discord staging test.**

In a non-production guild:

1. Invite the bot with required moderation/message permissions.
2. Run `/config watchchannel <channelId>` as Administrator.
3. Run `/config policy permissive`.
4. Send a message in the watched channel and verify no ban occurs, the event is reported, and the database records detection.
5. Change to `/config policy enforced`.
6. Send another test message and verify exactly one ban attempt, persistent record, and report.
7. Run `/status` and verify it responds.
8. Restart the process and verify configuration persists.

- [x] **Step 10: Run the production smoke test after restart.**

Verify startup logs show successful database initialization, Discord login, command registration, guild count, and status initialization without exposing secrets.

- [x] **Step 11: Commit final hardening only after verification.**

```bash
git status --short
git diff --check
git add .
git commit -m "chore: finalize BIBC production release"
```

Do not claim the implementation is complete until the verification output is actually clean.

---

## Required Acceptance Criteria

The implementation is accepted only when all of the following are true:

1. A guild can persistently configure exactly one watch channel through `/config watchchannel <id>`.
2. A guild can persistently choose `enforced` or `permissive` through `/config policy <enforced|permissive>`.
3. Guild A's configuration cannot alter Guild B's configuration.
4. Configuration survives process restart.
5. `enforced` attempts the existing ban behavior with the existing five-minute deletion window.
6. `permissive` records/reports detection without banning.
7. Successful bans are stored persistently and can be counted by week and month.
8. Failed ban attempts do not inflate successful-ban statistics.
9. `/info` is replaced by `/status`.
10. `/status` reports persistent operational information without relying on `bannedUsers` runtime state.
11. Bot activity uses exactly `Status type: watching, [#] servers - [#] members` with real runtime counts.
12. The Discord token is read from `.env` and never hard-coded.
13. `.env.example` exists and contains no real secret.
14. `.env` and runtime database files are ignored by Git.
15. Production logging uses `logging`, not uncontrolled `print()` output.
16. A failure to send a report does not undo or misclassify a successful ban.
17. Discord permission/hierarchy/API errors are handled without crashing the message watcher.
18. Database writes are transaction-safe and the database connection is closed on shutdown.
19. The event path has bounded duplicate protection and no unbounded ban-user list.
20. Full automated tests pass and the manual staging smoke test succeeds.

## Final Self-Review Checklist

- [x] Spec coverage: every approved feature has one or more implementation tasks.
- [x] Issues: every issue identified during source review has a corresponding fix path.
- [x] Security: `.env`, `.env.example`, Git ignore rules, and secret-safe logging are covered.
- [x] Persistence: guild config and ban history survive restart.
- [x] Statistics: weekly/monthly successful-ban counts are database-backed.
- [x] Commands: `/config` and `/status` are explicitly covered; legacy command removal is covered.
- [x] Status: exact required activity format is covered.
- [x] Reliability: lifecycle, Discord failures, database failures, reporting isolation, and bounded runtime state are covered.
- [x] Testing: unit, repository, service, integration, lifecycle, security/quality, and staging checks are covered.
- [x] Placeholder scan: no `TBD`, `TODO`, or instructionless "add appropriate handling" placeholders remain.
- [x] Interface consistency: repository/service method names are defined before later tasks consume them.
