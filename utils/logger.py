from loguru import logger
import sys
import os

logger.remove(0)

logger.add(
    sys.stderr, 
    level=os.getenv("LOG_LEVEL", "DEBUG"), 
    serialize=True,
    backtrace=True,
    diagnose=True,
    enqueue=True,  # Thread-safe async logging
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} | {message}",
)

def _safe_serialize(obj):
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)[:10000]  # Truncate long strings


def _log_fields(**kwargs):
    return {k: _safe_serialize(v) for k, v in kwargs.items() if v is not None}