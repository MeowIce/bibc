import os
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass(frozen=True)
class AppConfig:
    discordToken: str
    databasePath: str = "./data/bibc.db"

def loadConfig(envPath=None, loadEnv=True) -> AppConfig:
    if loadEnv:
        if envPath:
            load_dotenv(dotenv_path=envPath, override=True)
        else:
            load_dotenv()
            
    token = os.getenv("DISCORD_TOKEN")
    if not token or not token.strip():
        raise ValueError("DISCORD_TOKEN environment variable is required")
        
    dbPath = os.getenv("DATABASE_PATH", "./data/bibc.db")
    return AppConfig(discordToken=token.strip(), databasePath=dbPath)
