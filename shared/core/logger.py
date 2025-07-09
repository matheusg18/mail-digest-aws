import json
import sys
import traceback

from loguru import logger as loguru_logger

from shared.core.settings import settings

loguru_logger.remove()

if settings.LOG_FORMAT == "text":
    loguru_logger.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{extra[request_id]}</cyan> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        level="INFO",
        colorize=True,
    )
else:

    def gcp_formatter(record):
        severity_map = {
            "TRACE": "DEBUG",
            "DEBUG": "DEBUG",
            "INFO": "INFO",
            "SUCCESS": "INFO",
            "WARNING": "WARNING",
            "ERROR": "ERROR",
            "CRITICAL": "CRITICAL",
        }

        log_payload = {
            "message": record["message"],
            "severity": severity_map.get(record["level"].name, "INFO"),
            "source": {
                "module": record["module"],
                "function": record["function"],
                "line": record["line"],
            },
            **record["extra"],
        }

        if record["exception"]:
            log_payload["exception"] = "".join(
                traceback.format_exception(
                    record["exception"].type,
                    record["exception"].value,
                    record["exception"].traceback,
                )
            )

        return json.dumps(log_payload) + "\n"

    loguru_logger.add(
        sink=lambda msg: sys.stderr.write(gcp_formatter(msg.record)),  # type: ignore
        level="INFO",
    )


def L(request_id: str = "local"):
    return loguru_logger.bind(request_id=request_id)


__all__ = ["L"]
