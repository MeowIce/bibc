from datetime import datetime, timezone
from database import Database, formatUtc, parseUtc
from models.guildConfig import GuildConfig, ALLOWED_POLICIES

class GuildConfigRepository:
    def __init__(self, database: Database):
        self.database = database

    def get(self, guildId: int) -> GuildConfig | None:
        conn = self.database.connect()
        cursor = conn.execute(
            "SELECT guild_id, watch_channel_id, policy, report_channel_id, created_at, updated_at FROM guild_configs WHERE guild_id = ?",
            (guildId,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return GuildConfig(
            guildId=row["guild_id"],
            watchChannelId=row["watch_channel_id"],
            policy=row["policy"],
            reportChannelId=row["report_channel_id"],
            createdAt=parseUtc(row["created_at"]),
            updatedAt=parseUtc(row["updated_at"])
        )

    def upsertWatchChannel(self, guildId: int, channelId: int) -> GuildConfig:
        nowStr = formatUtc(datetime.now(timezone.utc))
        conn = self.database.connect()
        with conn:
            existing = self.get(guildId)
            if existing is None:
                conn.execute(
                    "INSERT INTO guild_configs (guild_id, watch_channel_id, policy, report_channel_id, created_at, updated_at) VALUES (?, ?, 'enforced', NULL, ?, ?)",
                    (guildId, channelId, nowStr, nowStr)
                )
            else:
                conn.execute(
                    "UPDATE guild_configs SET watch_channel_id = ?, updated_at = ? WHERE guild_id = ?",
                    (channelId, nowStr, guildId)
                )
        return self.get(guildId)

    def updatePolicy(self, guildId: int, policy: str) -> GuildConfig:
        if policy not in ALLOWED_POLICIES:
            raise ValueError(f"Invalid policy '{policy}'. Must be one of {ALLOWED_POLICIES}")
        nowStr = formatUtc(datetime.now(timezone.utc))
        conn = self.database.connect()
        with conn:
            existing = self.get(guildId)
            if existing is None:
                conn.execute(
                    "INSERT INTO guild_configs (guild_id, watch_channel_id, policy, report_channel_id, created_at, updated_at) VALUES (?, NULL, ?, NULL, ?, ?)",
                    (guildId, policy, nowStr, nowStr)
                )
            else:
                conn.execute(
                    "UPDATE guild_configs SET policy = ?, updated_at = ? WHERE guild_id = ?",
                    (policy, nowStr, guildId)
                )
        return self.get(guildId)

    def upsertReportChannel(self, guildId: int, channelId: int) -> GuildConfig:
        nowStr = formatUtc(datetime.now(timezone.utc))
        conn = self.database.connect()
        with conn:
            existing = self.get(guildId)
            if existing is None:
                conn.execute(
                    "INSERT INTO guild_configs (guild_id, watch_channel_id, policy, report_channel_id, created_at, updated_at) VALUES (?, NULL, 'enforced', ?, ?, ?)",
                    (guildId, channelId, nowStr, nowStr)
                )
            else:
                conn.execute(
                    "UPDATE guild_configs SET report_channel_id = ?, updated_at = ? WHERE guild_id = ?",
                    (channelId, nowStr, guildId)
                )
        return self.get(guildId)
