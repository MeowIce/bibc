from dataclasses import dataclass, field
from datetime import datetime, timezone

@dataclass
class BanRecord:
    guildId: int
    userId: int
    username: str
    channelId: int
    messageId: int
    policy: str
    action: str
    reason: str
    id: int | None = None
    createdAt: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
