"""OnShape credential handling."""

import os

from genbot.log import err


def get_credentials() -> dict:
    """Read ONSHAPE_API_KEY / ONSHAPE_API_SECRET from environment variables"""
    key = os.environ.get("ONSHAPE_API_KEY")
    secret = os.environ.get("ONSHAPE_API_SECRET")

    if not key or not secret:
        err(
            "OnShape credentials not found.\n"
            "  Set ONSHAPE_API_KEY and ONSHAPE_API_SECRET environment variables."
        )

    return {"key": key, "secret": secret}
