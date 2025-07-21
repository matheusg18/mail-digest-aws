import json
import sys
import traceback
from contextvars import ContextVar

from loguru import logger

from shared.core.settings import settings

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="-")

logger.remove()

if settings.LOG_FORMAT == "text":
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<magenta>{extra[trace_id]}</magenta> - "
            "<level>{message}</level>"
        ),
        level="INFO",
        colorize=True,
        filter=lambda record: record["extra"].update({"trace_id": trace_id_var.get()}) or True,
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

    logger.add(
        sink=lambda msg: sys.stderr.write(gcp_formatter(msg.record)),  # type: ignore
        level="INFO",
        filter=lambda record: record["extra"].update({"trace_id": trace_id_var.get()}) or True,
    )
