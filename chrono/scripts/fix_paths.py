#!/usr/bin/env python3
"""
Rewrites the container workspace prefix in compile_commands.json to the
actual host path. Run on the host after 'make vendor'.
"""

from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent
db_file = root / "chrono/build/compile_commands.json"

content = db_file.read_text()
content = content.replace("/home/trickfire/simulations/", str(root) + "/")
db_file.write_text(content)
print(f"Updated {db_file.relative_to(root)}")
