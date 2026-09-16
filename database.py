import os
import sqlite3
from datetime import datetime, timezone

class Database:
    def __init__(self, path: str):
        self.path = path
        self._connection = None

    def connect(self) -> sqlite3.Connection:
        if self._connection is None:
            directory = os.path.dirname(self.path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            conn = sqlite3.connect(self.path, timeout=5.0)
            conn.execute("PRAGMA foreign_keys = ON")
            conn.row_factory = sqlite3.Row
            self._connection = conn
        return self._connection

    def initialize(self) -> None:
        conn = self.connect()
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS guild_configs (
                    guild_id INTEGER PRIMARY KEY,
                    watch_channel_id INTEGER,
                    policy TEXT NOT NULL CHECK(policy IN ('enforced', 'permissive')),
                    report_channel_id INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ban_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    channel_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    policy TEXT NOT NULL,
                    action TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ban_records_guild_created ON ban_records(guild_id, created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ban_records_created ON ban_records(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ban_records_guild_user ON ban_records(guild_id, user_id)")

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

def formatUtc(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def parseUtc(dtStr: str) -> datetime:
    return datetime.strptime(dtStr, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
