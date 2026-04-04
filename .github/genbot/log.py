"""Logging class"""

import sys
from typing import NoReturn


def info(msg: str) -> None:
    """Info log"""
    print(f"[genbot] {msg}")


def warn(msg: str) -> None:
    """Warn log"""
    print(f"[genbot] WARN: {msg}")


def err(msg: str) -> NoReturn:
    """Error log, sys exits with 1"""
    print(f"[genbot] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)
