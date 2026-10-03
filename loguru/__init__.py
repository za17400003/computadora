"""
Minimal local shim for `loguru` used by Golem when the real
`loguru` package is not installed. This allows the application to run
and print logs using Python's standard `logging` as a fallback.

This module intentionally implements a very small subset of Loguru's
API used by the project: `logger.remove()`, `logger.add(...)`, and
`logger.debug/info/warning/error/exception`.
"""

import sys
import logging
from typing import Any
from pathlib import Path

_pylogger = logging.getLogger("computadora_app")
_pylogger.setLevel(logging.DEBUG)
_pylogger.propagate = False

_formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s - %(message)s", datefmt="%H:%M:%S")

_handlers = []

def remove():
    """Remove all configured handlers."""
    global _handlers
    for h in list(_handlers):
        try:
            _pylogger.removeHandler(h)
        except Exception:
            pass
    _handlers = []


def add(sink: Any, format: str | None = None, level: str = "DEBUG", **kwargs):
    """Add a simple handler. Accepts a file path, a file-like object or
    `sys.stderr`.

    Ignores Loguru-specific kwargs like `rotation` and `retention`.
    Returns the handler object (not an int id).
    """
    h = None
    lvl = getattr(logging, str(level).upper(), logging.DEBUG)

    try:
        if sink is sys.stderr:
            h = logging.StreamHandler(sys.stderr)
        elif hasattr(sink, "write"):
            # file-like
            h = logging.StreamHandler(sink)
        else:
            # treat as path-like or str
            path = str(sink)
            # If path contains braces (loguru time formatting), leave it as-is
            try:
                p = Path(path)
                # Ensure parent dir exists
                if p.parent:
                    p.parent.mkdir(parents=True, exist_ok=True)
                h = logging.FileHandler(path, encoding=kwargs.get("encoding", "utf-8"))
            except Exception:
                h = logging.StreamHandler(sys.stderr)
    except Exception:
        h = logging.StreamHandler(sys.stderr)

    h.setLevel(lvl)
    h.setFormatter(_formatter)
    _pylogger.addHandler(h)
    _handlers.append(h)
    return h


class Logger:
    def remove(self):
        remove()

    def add(self, sink: Any, format: str | None = None, level: str = "DEBUG", **kwargs):
        return add(sink, format=format, level=level, **kwargs)

    def debug(self, msg: str, *args, **kwargs):
        _pylogger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        _pylogger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        _pylogger.warning(msg, *args, **kwargs)

    def warn(self, msg: str, *args, **kwargs):
        _pylogger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        _pylogger.error(msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs):
        _pylogger.exception(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        _pylogger.critical(msg, *args, **kwargs)


# Export a module-level `logger` to emulate `from loguru import logger`
logger = Logger()

# Backwards compatibility: allow `from loguru import logger as logger`
__all__ = ["logger", "remove", "add"]
