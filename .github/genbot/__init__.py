"""genbot"""

from pathlib import Path

PACKAGE_DIR = Path(__file__).parent
TEMPLATES = PACKAGE_DIR / "templates"
REPO_ROOT = PACKAGE_DIR.parent.parent
ROBOTS_JSON = REPO_ROOT / "robots.json"
