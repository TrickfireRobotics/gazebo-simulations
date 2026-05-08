"""Simple loader for remote_pcs.json

Usage:
    from remote_pcs import load
    pcs = load()
    print(pcs["nvidia_pcs"]["orin"])  # -> 192.168.0.211
"""

from pathlib import Path
import json

_DATA_PATH = Path(__file__).with_suffix(".json")


def load():
    """Return parsed JSON data as a dict."""
    return json.loads(_DATA_PATH.read_text(encoding="utf-8"))


__all__ = ["load"]
