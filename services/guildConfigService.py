from models.guildConfig import GuildConfig, ALLOWED_POLICIES
from repositories.guildConfigRepository import GuildConfigRepository

class GuildConfigService:
    def __init__(self, repository: GuildConfigRepository):
        self.repository = repository

    def getConfig(self, guildId: int) -> GuildConfig | None:
        if not guildId or guildId <= 0:
            raise ValueError("Invalid guild ID")
        return self.repository.get(guildId)

    def setWatchChannel(self, guildId: int, channelId: int) -> GuildConfig:
        if not guildId or guildId <= 0:
            raise ValueError("Invalid guild ID")
        if not channelId or channelId <= 0:
            raise ValueError("Invalid channel ID")
        return self.repository.upsertWatchChannel(guildId, channelId)

    def setPolicy(self, guildId: int, policy: str) -> GuildConfig:
        if not guildId or guildId <= 0:
            raise ValueError("Invalid guild ID")
        if policy not in ALLOWED_POLICIES:
            raise ValueError(f"Invalid policy '{policy}'. Must be one of {ALLOWED_POLICIES}")
        return self.repository.updatePolicy(guildId, policy)

    def setReportChannel(self, guildId: int, channelId: int) -> GuildConfig:
        if not guildId or guildId <= 0:
            raise ValueError("Invalid guild ID")
        if not channelId or channelId <= 0:
            raise ValueError("Invalid channel ID")
        return self.repository.upsertReportChannel(guildId, channelId)
