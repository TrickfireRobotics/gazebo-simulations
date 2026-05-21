"""Discord Rich Presence (DRPC) integration for TrickFire Simulation"""

import os
import sys
import time

from pypresence import Presence


def _find_discord_socket_dir() -> str | None:
    """Return the directory containing a discord-ipc-N socket, or None if not found."""
    candidates = [
        os.environ.get("XDG_RUNTIME_DIR"),  # standard Linux user session
        os.environ.get("TMPDIR"),
        "/run/host-runtime",  # devcontainer: host XDG_RUNTIME_DIR mounted here
        "/run/user/1000",  # fallback for some Linux distros
        "/tmp",
    ]
    for base in filter(None, candidates):
        for i in range(10):
            if os.path.exists(os.path.join(base, f"discord-ipc-{i}")):
                return base
    return None


def rpc_start(is_docker: bool = False, robot_name: str = "Unknown Robot") -> None:
    """Start DRPC in a separate thread"""
    try:
        if sys.platform == "linux":
            socket_dir = _find_discord_socket_dir()
            if socket_dir is None:
                print("Discord RPC unavailable: no Discord IPC socket found")
                return
            # pypresence checks TMPDIR early in its path search; point it at the socket dir
            # so it works both natively and inside the devcontainer (/run/host-runtime).
            os.environ["TMPDIR"] = socket_dir

        client_id = "1504990746527404063"
        rpc = Presence(client_id)
        rpc.connect()
        rpc.update(
            name="TrickFire Simulation (" + robot_name + ")",
            details="Running TrickFire Simulation on " + robot_name,
            state="Running in Docker" if is_docker else "Running locally",
        )
        while True:
            time.sleep(15)
    except Exception as e:  # pylint: disable=broad-except
        print(f"Discord RPC unavailable: {e}")
