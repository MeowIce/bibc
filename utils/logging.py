import logging
import sys
import time

def configureLogging(logLevel=logging.INFO):
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    formatter.converter = time.gmtime

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    rootLogger = logging.getLogger()
    rootLogger.setLevel(logLevel)

    rootLogger.handlers.clear()
    rootLogger.addHandler(handler)
    return rootLogger

def truncateContent(content: str, maxLength: int = 100) -> str:
    if not content:
        return ""
    if len(content) <= maxLength:
        return content
    return content[:maxLength] + "..."
