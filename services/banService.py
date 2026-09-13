from dataclasses import dataclass
import logging
import discord
from models.guildConfig import GuildConfig
from models.banRecord import BanRecord
from repositories.banRepository import BanRepository

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class BanResult:
    action: str
    reason: str

class BanService:
    def __init__(self, banRepository: BanRepository, defaultReason: str = "gửi tin nhắn vào kênh lọc spam"):
        self.banRepository = banRepository
        self.defaultReason = defaultReason

    async def handleMessage(self, message: discord.Message, guildConfig: GuildConfig) -> BanResult:
        if guildConfig.policy == "permissive":
            action = "detected"
            reason = "permissive policy log only"
            record = BanRecord(
                guildId=message.guild.id,
                userId=message.author.id,
                username=str(message.author),
                channelId=message.channel.id,
                messageId=message.id,
                policy=guildConfig.policy,
                action=action,
                reason=reason
            )
            self.banRepository.insert(record)
            return BanResult(action=action, reason=reason)

        if getattr(message.guild, "owner_id", None) == message.author.id:
            action = "failed"
            reason = "Cannot ban server owner"
            record = BanRecord(
                guildId=message.guild.id,
                userId=message.author.id,
                username=str(message.author),
                channelId=message.channel.id,
                messageId=message.id,
                policy=guildConfig.policy,
                action=action,
                reason=reason
            )
            self.banRepository.insert(record)
            return BanResult(action=action, reason=reason)

        guildMe = getattr(message.guild, "me", None)
        if guildMe is not None:
            authorTopRole = getattr(message.author, "top_role", None)
            meTopRole = getattr(guildMe, "top_role", None)
            if authorTopRole is not None and meTopRole is not None:
                try:
                    if authorTopRole >= meTopRole:
                        action = "failed"
                        reason = "Role hierarchy prevents ban"
                        record = BanRecord(
                            guildId=message.guild.id,
                            userId=message.author.id,
                            username=str(message.author),
                            channelId=message.channel.id,
                            messageId=message.id,
                            policy=guildConfig.policy,
                            action=action,
                            reason=reason
                        )
                        self.banRepository.insert(record)
                        return BanResult(action=action, reason=reason)
                except TypeError:
                    pass

        try:
            await message.guild.ban(
                message.author,
                reason=self.defaultReason,
                delete_message_seconds=300
            )
            action = "banned"
            reason = self.defaultReason
        except discord.Forbidden as e:
            action = "failed"
            reason = f"Forbidden: {getattr(e, 'text', str(e))}"
            logger.warning(f"Forbidden while banning user {message.author.id} in guild {message.guild.id}: {reason}")
        except discord.HTTPException as e:
            action = "failed"
            reason = f"HTTPException: {getattr(e, 'text', str(e))}"
            logger.error(f"HTTP error while banning user {message.author.id} in guild {message.guild.id}: {reason}")
        except Exception as e:
            action = "failed"
            reason = f"Error: {e}"
            logger.exception(f"Unexpected error while banning user {message.author.id} in guild {message.guild.id}")

        record = BanRecord(
            guildId=message.guild.id,
            userId=message.author.id,
            username=str(message.author),
            channelId=message.channel.id,
            messageId=message.id,
            policy=guildConfig.policy,
            action=action,
            reason=reason
        )
        self.banRepository.insert(record)
        return BanResult(action=action, reason=reason)
