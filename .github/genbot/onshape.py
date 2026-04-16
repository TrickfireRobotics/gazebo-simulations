"""Onshape API integration"""

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from genbot.credentials import get_credentials
from genbot.log import err, info

_ONSHAPE_URL_RE = re.compile(
    r"documents/([0-9a-f]+)/[wv]/([0-9a-f]+)/e/([0-9a-f]+)",
    re.IGNORECASE,
)


def parse_onshape_url(url: str) -> tuple:
    """Return (api_url, documentId, workspaceId, elementId) from an Onshape URL"""
    m = _ONSHAPE_URL_RE.search(url)
    if not m:
        err(
            f"Could not parse Onshape URL: {url}\n"
            "  Expected format: https://<host>/documents/<docId>/w/<wsId>/e/<elId>"
        )
    parsed = urlparse(url)
    api_url = f"{parsed.scheme}://{parsed.netloc}"
    return api_url, m.group(1), m.group(2), m.group(3)


def run_onshape_to_robot(
    doc_id: str, ws_id: str, el_id: str, api_url: str, creds: dict, workdir: Path
) -> None:
    """Write config.json and invoke onshape-to-robot in workdir"""
    config = {
        "documentId": doc_id,
        "workspaceId": ws_id,
        "elementId": el_id,
        "output_format": "urdf",
        "add_dummy_base_link": True,
    }
    (workdir / "config.json").write_text(json.dumps(config, indent=2))

    env = os.environ.copy()
    env["ONSHAPE_ACCESS_KEY"] = creds["key"]
    env["ONSHAPE_SECRET_KEY"] = creds["secret"]
    env["ONSHAPE_API"] = api_url

    subprocess.run(
        ["onshape-to-robot", "."],
        cwd=workdir,
        env=env,
        check=True,
    )


def download(robot: str, doc_id: str, ws_id: str, el_id: str, api_url: str) -> Path:
    """Run onshape-to-robot and return the working directory"""
    creds = get_credentials()
    tmpdir = Path(tempfile.mkdtemp(prefix="genbot_"))
    workdir = tmpdir / robot
    workdir.mkdir()
    info("Running onshape-to-robot...")
    run_onshape_to_robot(doc_id, ws_id, el_id, api_url, creds, workdir)
    return workdir
