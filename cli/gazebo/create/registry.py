"""robots.json registry"""

import json

from . import ROBOTS_JSON


def load_robots_json() -> list:
    if not ROBOTS_JSON.exists():
        return []
    raw = ROBOTS_JSON.read_text().strip()
    if not raw:
        save_robots_json([])
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        save_robots_json([])
        return []
    if not isinstance(data, list):
        save_robots_json([])
        return []
    return data


def save_robots_json(data: list) -> None:
    ROBOTS_JSON.write_text(json.dumps(data, indent=4) + "\n")
