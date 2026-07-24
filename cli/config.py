"""Local CLI configuration stored at ~/.config/trickfire/token.json

Priority order for auth:
  1. SIM_API_KEY env vars               (CI / automated)
  2. ~/.config/trickfire/token.json     (developer local, written by sim auth)
"""

import json
import os
from pathlib import Path

_CONFIG_DIR = Path.home() / ".config" / "trickfire"
_CONFIG_FILE = _CONFIG_DIR / "token.json"


def load() -> str:
    """Return configured api key"""
    env_key = os.environ.get("SIM_API_KEY")
    if env_key:
        return env_key

    if not _CONFIG_FILE.exists():
        return None
    try:
        data = json.loads(_CONFIG_FILE.read_text())
        if isinstance(data, dict):
            return data.get("api_key")
        return data
    except (json.JSONDecodeError, OSError):
        return None


def save(api_key: str) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _CONFIG_FILE.write_text(json.dumps({"api_key": api_key}, indent=2))
    _CONFIG_FILE.chmod(0o600)


def clear() -> None:
    if _CONFIG_FILE.exists():
        _CONFIG_FILE.unlink()
