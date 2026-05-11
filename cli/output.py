import sys
import os
from typing import Callable, NoReturn

try:
    _is_tty = os.isatty(sys.stdout.fileno())
except Exception:  # pylint: disable=broad-except
    _is_tty = False
if _is_tty:
    _B = "\033[1m"     # bold
    _C = "\033[1;36m"  # cyan  (info)
    _G = "\033[1;32m"  # green
    _Y = "\033[1;33m"  # yellow (warn)
    _R = "\033[1;31m"  # red    (fatal)
    _P = "\033[1;35m"  # purple (step)
    _D = "\033[2m"     # dim
    _X = "\033[0m"     # reset
    _TTY = True
else:
    _B = _C = _G = _Y = _R = _P = _D = _X = ""
    _TTY = False


def info(msg: str) -> None:
    """Informational message - print to stdout"""
    print(f"{_C}[INFO]{_X}  {msg}")


def warn(msg: str) -> None:
    """Non-fatal warning - print message to stderr"""
    print(f"{_Y}[WARN]{_X}  {msg}", file=sys.stderr)


def die(msg: str) -> NoReturn:
    """Fatal error - print message and exit with code 1"""
    print(f"\n{_R}[FATAL]{_X}  {msg}\n", file=sys.stderr)
    sys.exit(1)


def run_step(label: str, fn: Callable[[], None]) -> None:
    """Run a step with a label, showing progress and handling exceptions"""
    print(f"{_P}[STEP]{_X} {label}")
    if _TTY:
        # Save cursor position
        print("\0337", end="", flush=True)
    try:
        fn()
        if _TTY:
            # Restore cursor and clear from cursor to end of line
            print("\0338\033[J", end="", flush=True)
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception:
        print(f"\n{_R}[FATAL]{_X}  {label} - failed\n", file=sys.stderr)
        raise
