from dataclasses import dataclass, field
from datetime import datetime, timezone

ALLOWED_POLICIES = {"enforced", "permissive"}

@dataclass
class GuildConfig:
    guildId: int
    watchChannelId: int | None = None
    policy: str = "enforced"
    reportChannelId: int | None = None
    createdAt: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if self.policy not in ALLOWED_POLICIES:
            raise ValueError(f"Invalid policy '{self.policy}'. Must be one of {ALLOWED_POLICIES}")
