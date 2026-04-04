"""robots.json registry file"""

import json

from genbot import ROBOTS_JSON


def load_robots_json() -> list:
    """Load the robot registry"""
    if not ROBOTS_JSON.exists():
        return []
    return json.loads(ROBOTS_JSON.read_text())


def save_robots_json(data: list) -> None:
    """Write the robot registry"""
    ROBOTS_JSON.write_text(json.dumps(data, indent=4) + "\n")
