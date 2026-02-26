"""
leosetter/updater.py
────────────────────
In-app update checker for LeoSetter.

Flow:
  1. fetch_latest_version()  — hits GitHub API, returns (tag_str, download_url)
  2. is_newer(remote, local) — compares SemVer tuples
  3. download_update()       — streams the installer EXE to a temp file, returns path
  4. launch_installer()      — runs the installer and quits the app

All network calls are done off the main thread by the caller (app.py).
"""

import re
import sys
import os
import subprocess
import tempfile
import urllib.request
import urllib.error
import json
from typing import Tuple, Optional

from .version import APP_VERSION, API_LATEST


# ── version helpers ───────────────────────────────────────────────────────────

def _parse_version(tag: str) -> Tuple[int, ...]:
    """Parse a tag like 'v1.2.3' or '1.2.3' into (1, 2, 3)."""
    cleaned = re.sub(r"[^0-9.]", "", tag)
    parts = cleaned.split(".")
    try:
        return tuple(int(p) for p in parts if p)
    except ValueError:
        return (0,)


def is_newer(remote_tag: str, local_version: str = APP_VERSION) -> bool:
    """Return True if remote_tag represents a version newer than local_version."""
    return _parse_version(remote_tag) > _parse_version(local_version)


# ── network ───────────────────────────────────────────────────────────────────

def fetch_latest_release(timeout: int = 10) -> Tuple[str, Optional[str]]:
    """
    Query the GitHub API for the latest release.

    Returns:
        (tag_name, asset_download_url)  — asset_download_url is the first .exe asset,
        or None if no exe asset exists.

    Raises:
        RuntimeError on network / JSON parse errors.
    """
    req = urllib.request.Request(
        API_LATEST,
        headers={"User-Agent": "LeoSetter-updater/1.0", "Accept": "application/vnd.github+json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error: {exc.reason}") from exc
    except Exception as exc:
        raise RuntimeError(f"Failed to reach GitHub: {exc}") from exc

    tag = data.get("tag_name", "").strip()
    if not tag:
        raise RuntimeError("GitHub response did not contain a tag_name.")

    # Find the first .exe asset attached to the release
    assets = data.get("assets", [])
    exe_url: Optional[str] = None
    for asset in assets:
        name = asset.get("name", "").lower()
        if name.endswith(".exe"):
            exe_url = asset.get("browser_download_url")
            break

    return tag, exe_url


# ── download ──────────────────────────────────────────────────────────────────

def download_update(
    url: str,
    progress_callback=None,
) -> str:
    """
    Download the installer from *url* to a temp file.

    progress_callback(downloaded_bytes, total_bytes) — called periodically.
    Returns the path to the downloaded file.
    """
    suffix = ".exe"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="LeoSetterSetup_")
    tmp_path = tmp.name

    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "LeoSetter-updater/1.0"}
        )
        with urllib.request.urlopen(req) as resp, open(tmp_path, "wb") as out:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            block = 65536
            while True:
                chunk = resp.read(block)
                if not chunk:
                    break
                out.write(chunk)
                downloaded += len(chunk)
                if progress_callback:
                    progress_callback(downloaded, total)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

    return tmp_path


# ── launch ────────────────────────────────────────────────────────────────────

def launch_installer(installer_path: str):
    """
    Run the downloaded installer and then exit the current application.
    The installer is run detached so it outlives the parent process.
    """
    if sys.platform == "win32":
        # DETACHED_PROCESS = 8  — lets the installer keep running after we exit
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        DETACHED_PROCESS = 0x00000008
        subprocess.Popen(
            [installer_path],
            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
            close_fds=True,
        )
    else:
        subprocess.Popen([installer_path])
    # Exit current instance so the installer can overwrite the EXE
    sys.exit(0)
