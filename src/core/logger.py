import os
import sys

from loguru import logger as loguru_logger

loguru_logger.remove()

is_local = os.environ.get("AWS_SAM_LOCAL") == "true"

if is_local:
    loguru_logger.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> -"
            " <level>{message}</level>"
        ),
        level="INFO",
        colorize=True,
    )
else:
    loguru_logger.add(sys.stderr, serialize=True, level="INFO")


def L(request_id: str = "local"):
    return loguru_logger.bind(request_id=request_id)


__all__ = ["L", "loguru_logger"]
