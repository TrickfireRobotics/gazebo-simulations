"""sim auth - configure dashboard API key for OnShape access"""

import sys

import requests

from . import config as cfg
from .output import die, info

DASHBOARD_URL = "https://dashboard.trickfirerobotics.com"


def auth() -> None:
    key_input = cfg.load()

    if not key_input:
        print()
        print(f"Go to {DASHBOARD_URL}/settings → 'CLI access' to generate a key.")
        print()
        try:
            key_input = input("Paste your API key: ").strip()
        except (KeyboardInterrupt, EOFError):
            sys.exit(130)

        if not key_input:
            die("API key is required!")

    info("Verifying...")
    try:
        resp = requests.post(
            f"{DASHBOARD_URL}/api/service/verify",
            headers={"x-api-key": key_input},
            timeout=10,
        )
    except requests.ConnectionError:
        die(f"Could not connect to {DASHBOARD_URL}. Check your network connection")
    except requests.Timeout:
        die("Connection timed out")

    if resp.status_code == 401:
        die("Invalid API key! Generate a new one at Settings → CLI access.")
    if not resp.ok:
        die(f"Verification failed ({resp.status_code}). Check the dashboard URL.")

    data = resp.json()
    name = data.get("name", "unknown")

    cfg.save(key_input)
    print()
    info(f"Authenticated as: {name}")
    info(f"Saved to {cfg._CONFIG_FILE}")
