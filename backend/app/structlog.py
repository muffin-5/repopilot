"""
Graceful fallback shim for structlog.

Provides standard library logging wrapper with structlog-compatible get_logger().
If real structlog is installed, it delegates to real structlog.
"""

from __future__ import annotations

import logging
import sys
from typing import Any


class StandardLoggerAdapter:
    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def info(self, event: str, **kwargs: Any) -> None:
        self._log(logging.INFO, event, kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        self._log(logging.WARNING, event, kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        self._log(logging.ERROR, event, kwargs)

    def debug(self, event: str, **kwargs: Any) -> None:
        self._log(logging.DEBUG, event, kwargs)

    def _log(self, level: int, event: str, kwargs: dict[str, Any]) -> None:
        if kwargs:
            extra_str = " ".join(f"{k}={v}" for k, v in kwargs.items())
            self._logger.log(level, f"{event} | {extra_str}")
        else:
            self._logger.log(level, event)


def get_logger(name: str = "") -> Any:
    # Check if real structlog is installed outside
    # (avoid importing self recursively)
    for mod_name, mod in list(sys.modules.items()):
        if mod_name == "structlog" and getattr(mod, "__file__", "") != __file__:
            return mod.get_logger(name)

    logger = logging.getLogger(name or "repopilot")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return StandardLoggerAdapter(logger)
