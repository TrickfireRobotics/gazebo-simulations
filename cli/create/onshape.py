"""OnShape export via dashboard proxy"""

import re
import tarfile
import tempfile
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

from .. import config as cfg
from ..auth import DASHBOARD_URL
from ..output import die as err, info

_ONSHAPE_URL_RE = re.compile(
    r"documents/([0-9a-f]+)/[wv]/([0-9a-f]+)/e/([0-9a-f]+)",
    re.IGNORECASE,
)

_POLL_INTERVAL = 5  # seconds between status checks
_POLL_TIMEOUT = 8 * 60  # give up after 8 minutes


def parse_onshape_url(url: str) -> tuple:
    m = _ONSHAPE_URL_RE.search(url)
    if not m:
        err(
            f"Could not parse OnShape URL: {url}\n"
            "  Expected format: https://<host>/documents/<docId>/w/<wsId>/e/<elId>"
        )
    parsed = urlparse(url)
    api_url = f"{parsed.scheme}://{parsed.netloc}"
    return api_url, m.group(1), m.group(2), m.group(3)


def _poll_job(dashboard_url: str, job_id: str) -> requests.Response:
    """Poll until the job is done; returns the streaming archive response."""
    deadline = time.monotonic() + _POLL_TIMEOUT
    while time.monotonic() < deadline:
        time.sleep(_POLL_INTERVAL)
        try:
            resp = requests.get(
                f"{dashboard_url}/api/sim/export/{job_id}",
                stream=True,
                timeout=30,
            )
        except requests.ConnectionError:
            err(f"Lost connection to {dashboard_url} while waiting for export.")
        except requests.Timeout:
            err("Timed out polling export status.")

        if resp.status_code == 202:
            continue  # still running
        return resp

    err(f"Export did not complete within {_POLL_TIMEOUT // 60} minutes.")


def download(
    robot: str, doc_id: str, ws_id: str, el_id: str, api_url: str, *, force_refresh: bool = False
) -> Path:
    api_key = cfg.load()
    if not api_key:
        err(
            "Not authenticated. Run 'sim auth' to configure dashboard access.\n"
            " └─ You'll need an account at the TrickFire dashboard."
        )

    dashboard_url = DASHBOARD_URL

    info("Requesting export from dashboard (may take a few minutes if not cached)...")

    try:
        resp = requests.post(
            f"{dashboard_url}/api/sim/export",
            json={
                "onshapeUrl": f"{api_url}/documents/{doc_id}/w/{ws_id}/e/{el_id}",
                "forceRefresh": force_refresh,
            },
            headers={"x-api-key": api_key},
            stream=True,
            timeout=30,
        )
    except requests.ConnectionError:
        err(f"Could not connect to {dashboard_url}. Check your network connection.")
    except requests.Timeout:
        err("Export request timed out.")

    if resp.status_code == 401:
        err("API key rejected. Run 'sim auth' to re-authenticate.")
    if resp.status_code == 503:
        err("OnShape is not configured on the dashboard server. Contact an admin.")

    if resp.status_code == 202:
        job_id = resp.json().get("jobId")
        if not job_id:
            err("Server returned 202 but no jobId.")
        info("Export job started, waiting for onshape-to-robot to complete...")
        resp = _poll_job(dashboard_url, job_id)

    if not resp.ok:
        try:
            msg = resp.json().get("error", resp.text)
        except Exception:
            msg = resp.text
        err(f"Export failed ({resp.status_code}): {msg}")

    tmpdir = Path(tempfile.mkdtemp(prefix="sim_"))
    workdir = tmpdir / robot
    workdir.mkdir()

    archive_path = tmpdir / "export.tar.gz"
    info("Downloading export archive...")
    with open(archive_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=65536):
            f.write(chunk)

    info("Extracting...")
    with tarfile.open(archive_path, "r:gz") as tf:
        tf.extractall(workdir)

    archive_path.unlink()
    return workdir
