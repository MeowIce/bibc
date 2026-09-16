from datetime import datetime
from database import Database, formatUtc, parseUtc
from models.banRecord import BanRecord

class BanRepository:
    def __init__(self, database: Database):
        self.database = database

    def insert(self, record: BanRecord) -> BanRecord:
        conn = self.database.connect()
        createdStr = formatUtc(record.createdAt)
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO ban_records (
                    guild_id, user_id, username, channel_id, message_id, policy, action, reason, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.guildId,
                    record.userId,
                    record.username,
                    record.channelId,
                    record.messageId,
                    record.policy,
                    record.action,
                    record.reason,
                    createdStr
                )
            )
            record.id = cursor.lastrowid
        return record

    def countSince(self, startTime: datetime, guildId: int | None = None, action: str = "banned") -> int:
        conn = self.database.connect()
        startStr = formatUtc(startTime)
        if guildId is not None:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM ban_records WHERE created_at >= ? AND guild_id = ? AND action = ?",
                (startStr, guildId, action)
            )
        else:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM ban_records WHERE created_at >= ? AND action = ?",
                (startStr, action)
            )
        return cursor.fetchone()[0]

    def countUniqueUsersSince(self, startTime: datetime, guildId: int | None = None, action: str = "banned") -> int:
        conn = self.database.connect()
        startStr = formatUtc(startTime)
        if guildId is not None:
            cursor = conn.execute(
                "SELECT COUNT(DISTINCT user_id) FROM ban_records WHERE created_at >= ? AND guild_id = ? AND action = ?",
                (startStr, guildId, action)
            )
        else:
            cursor = conn.execute(
                "SELECT COUNT(DISTINCT user_id) FROM ban_records WHERE created_at >= ? AND action = ?",
                (startStr, action)
            )
        return cursor.fetchone()[0]

    def countTotal(self, guildId: int | None = None, action: str = "banned") -> int:
        conn = self.database.connect()
        if guildId is not None:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM ban_records WHERE guild_id = ? AND action = ?",
                (guildId, action)
            )
        else:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM ban_records WHERE action = ?",
                (action,)
            )
        return cursor.fetchone()[0]

    def getRecent(self, guildId: int | None = None, limit: int = 50) -> list[BanRecord]:
        conn = self.database.connect()
        if guildId is not None:
            cursor = conn.execute(
                """
                SELECT id, guild_id, user_id, username, channel_id, message_id, policy, action, reason, created_at
                FROM ban_records WHERE guild_id = ? ORDER BY id DESC LIMIT ?
                """,
                (guildId, limit)
            )
        else:
            cursor = conn.execute(
                """
                SELECT id, guild_id, user_id, username, channel_id, message_id, policy, action, reason, created_at
                FROM ban_records ORDER BY id DESC LIMIT ?
                """,
                (limit,)
            )
        rows = cursor.fetchall()
        return [
            BanRecord(
                id=row["id"],
                guildId=row["guild_id"],
                userId=row["user_id"],
                username=row["username"],
                channelId=row["channel_id"],
                messageId=row["message_id"],
                policy=row["policy"],
                action=row["action"],
                reason=row["reason"],
                createdAt=parseUtc(row["created_at"])
            )
            for row in rows
        ]
