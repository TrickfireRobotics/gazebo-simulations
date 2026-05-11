import sys
import os
from typing import Callable, NoReturn

try:
    _is_tty = os.isatty(sys.stdout.fileno())
except Exception:  # pylint: disable=broad-except
    _is_tty = False
if _is_tty:
    _B = "\033[1m"  # bold
    _G = "\033[1;32m"  # green
    _Y = "\033[1;33m"  # yellow
    _R = "\033[1;31m"  # red
    _P = "\033[1;35m"  # purple
    _D = "\033[2m"  # dim
    _X = "\033[0m"  # reset
    _TTY = True
else:
    _B = _G = _Y = _R = _P = _D = _X = ""
    _TTY = False


def info(msg: str) -> None:
    """Informational message - print to stdout"""
    print(f"{_B}[INFO]{_X}  {msg}")


def warn(msg: str) -> None:
    print(f"{_Y}[WARN]{_X}  {msg}", file=sys.stderr)


def die(msg: str) -> NoReturn:
    print(f"\n{_R}[FATAL]{_X}  {msg}\n", file=sys.stderr)
    sys.exit(1)


def run_step(label: str, fn: Callable[[], None]) -> None:
    print(f"{_P}[STEP]{_X} {label}")
    if _TTY:
        print("\0337", end="", flush=True)
    try:
        fn()
        if _TTY:
            print("\0338\033[J", end="", flush=True)
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception:
        print(f"\n{_R}[FATAL]{_X}  {label} - failed\n", file=sys.stderr)
        raise
