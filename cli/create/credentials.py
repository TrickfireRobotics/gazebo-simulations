"""OnShape credential handling"""

import os
from pathlib import Path

from ..output import die as err


def get_credentials() -> dict:
    """Get OnShape API credentials from environment variables or onshape.env file"""
    key = os.environ.get("ONSHAPE_API_KEY")
    secret = os.environ.get("ONSHAPE_API_SECRET")

    # If not in environment, try to load from onshape.env in current directory or cli/ subdirectory
    if not key or not secret:
        possible_paths = [
            Path("onshape.env"),
            Path("cli/onshape.env"),
            Path(__file__).parent.parent / "onshape.env",
        ]

        for env_file in possible_paths:
            if env_file.exists():
                with open(env_file, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            var_name, var_value = line.split("=", 1)
                            if var_name == "ONSHAPE_API_KEY":
                                key = var_value
                            elif var_name == "ONSHAPE_API_SECRET":
                                secret = var_value
                break

    if not key or not secret:
        err(
            "OnShape credentials not found.\n"
            " └─ Most users: use Actions → 'Create new robot' workflow instead\n"
            " └─ Developers: run sim auth to verify local access is set up"
        )

    return {"key": key, "secret": secret}
