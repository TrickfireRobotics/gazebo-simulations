"""sim login - decrypt Onshape credentials using SSH key"""

import shutil
import subprocess
from pathlib import Path

from .output import die, info

_CLI_DIR = Path(__file__).parent
_REPO_ROOT = _CLI_DIR.parent
_AGE_FILE = _REPO_ROOT / "onshape.env.age"
_ONSHAPE_ENV = _CLI_DIR / "onshape.env"

_SSH_KEY_CANDIDATES = [
    Path.home() / ".ssh" / "id_ed25519",
    Path.home() / ".ssh" / "id_rsa",
    Path.home() / ".ssh" / "id_ecdsa",
    Path.home() / ".ssh" / "id_dsa",
]


def login() -> None:
    if not shutil.which("age"):
        die(
            "age is not installed.\n"
            " └— macOS:  brew install age\n"
            " └— Linux:  sudo apt install age\n"
            " └— Other:  https://github.com/FiloSottile/age#installation"
        )

    if not _AGE_FILE.exists():
        die(
            "onshape.env.age not found — credentials haven't been encrypted yet.\n"
            " └— Add your GitHub username to authorized_users.jsonc and push to main.\n"
            "    CI will encrypt automatically."
        )

    for ssh_key in _SSH_KEY_CANDIDATES:
        if not ssh_key.exists():
            continue
        result = subprocess.run(
            ["age", "--decrypt", "--identity", str(ssh_key), str(_AGE_FILE)],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            _ONSHAPE_ENV.write_text(result.stdout)
            info(f"Credentials saved to cli/onshape.env — you can now run sim create")
            return

    die(
        "No SSH key matched the encrypted credentials.\n"
        " └— Make sure your GitHub username is in authorized_users.txt\n"
        " └— Ask a repo admin to push the change so CI re-encrypts"
    )
