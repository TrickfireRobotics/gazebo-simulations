"""sim login - decrypt Onshape credentials using SSH key"""

import shutil
import subprocess
from pathlib import Path

from .output import die, info, warn
from .paths import REPO_DIR

_AGE_FILE = REPO_DIR / "cli" / "onshape.env.age"
_ONSHAPE_ENV = REPO_DIR / "cli" / "onshape.env"

_SSH_KEY_CANDIDATES = [
    Path.home() / ".ssh" / "id_ed25519",
    Path.home() / ".ssh" / "id_rsa",
    Path.home() / ".ssh" / "id_ecdsa",
    Path.home() / ".ssh" / "id_dsa",
]


def login() -> None:
    """Decrypt onshape.env.age using age and save to onshape.env"""
    info("Checking for age...")
    if not shutil.which("age"):
        die(
            "age is not installed.\n"
            " └— macOS:  brew install age\n"
            " └— Linux:  sudo apt install age\n"
            " └— Other:  https://github.com/FiloSottile/age#installation"
        )
    info("age found")

    info(f"Looking for {_AGE_FILE.name}...")
    if not _AGE_FILE.exists():
        die(
            "onshape.env.age not found — credentials haven't been encrypted yet.\n"
            " └— Add your GitHub username to authorized_users.jsonc and push to main.\n"
            "    CI will encrypt automatically."
        )
    info(f"Found {_AGE_FILE.name}")

    present = [k for k in _SSH_KEY_CANDIDATES if k.exists()]
    missing = [k for k in _SSH_KEY_CANDIDATES if not k.exists()]

    if not present:
        die(
            "No SSH keys found. Checked:\n"
            + "\n".join(f" └— {k}" for k in _SSH_KEY_CANDIDATES)
            + "\n   Make sure your SSH key exists in ~/.ssh/"
        )

    info(f"Found {len(present)} SSH key(s): {', '.join(k.name for k in present)}")
    if missing:
        info(f"Skipping (not present): {', '.join(k.name for k in missing)}")

    no_access = False
    for ssh_key in present:
        info(f"Trying {ssh_key.name}...")
        result = subprocess.run(
            ["age", "--decrypt", "--identity", str(ssh_key), str(_AGE_FILE)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            _ONSHAPE_ENV.write_text(result.stdout)
            info("Credentials saved to cli/onshape.env — you can now run sim create")
            return

        stderr = result.stderr.strip()
        if "no identity matched" in stderr:
            warn(f"{ssh_key.name}: no access (key not a recipient)")
            no_access = True
        else:
            warn(f"{ssh_key.name}: decryption failed — {stderr or 'unknown error'}")

    if no_access:
        die(
            "Access denied — your SSH key is not an authorized recipient.\n"
            " └— Make sure your GitHub username is in authorized_users.jsonc\n"
            " └— Ask a repo admin to push the change so CI re-encrypts\n"
            " └— Then run sim login again"
        )
    else:
        die(
            "Decryption failed for all keys — something went wrong.\n"
            " └— Check the warnings above for details\n"
            " └— If the file is corrupt, ask a repo admin to re-run the reencrypt workflow"
        )
