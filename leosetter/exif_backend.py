import json
import os
import subprocess
import sys
import shutil
import logging
import re
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ── User-writable config directory ────────────────────────────────────────────
# Store templates and settings under %APPDATA%/LeoSetter (Windows) or
# ~/.config/LeoSetter (Linux/macOS) so writes always succeed even when the
# app is installed to a read-only location like Program Files.

def _user_config_dir() -> str:
    """Return a writable per-user config directory for LeoSetter."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.environ.get("XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config"))
    path = os.path.join(base, "LeoSetter")
    os.makedirs(path, exist_ok=True)
    return path


CONFIG_DIR     = _user_config_dir()
TEMPLATES_FILE = os.path.join(CONFIG_DIR, "templates.json")

# ── Template storage ──────────────────────────────────────────────────────────

def load_templates() -> Dict[str, Dict[str, str]]:
    if not os.path.exists(TEMPLATES_FILE):
        return {}
    try:
        with open(TEMPLATES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_templates(templates: Dict[str, Dict[str, str]]) -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(TEMPLATES_FILE, "w", encoding="utf-8") as f:
        json.dump(templates, f, indent=2, ensure_ascii=False)


# Mapping from our UI field names to exiftool tag names (prefer XMP where sane)
TAG_MAP = {
    # Description
    "Title":       ["EXIF:XPTitle", "XMP:Title", "IPTC:ObjectName", "EXIF:ImageDescription"],
    "Subject":     ["EXIF:XPSubject", "XMP:Headline"],
    "Rating":      ["XMP:Rating", "EXIF:Rating", "EXIF:RatingPercent"],
    "Tags":        ["EXIF:XPKeywords", "XMP:TagsList", "XMP:Subject", "IPTC:Keywords"],
    "Comments":    ["EXIF:XPComment", "XMP:Description", "EXIF:UserComment", "IPTC:Caption-Abstract"],
    # Origin
    "Authors":     ["EXIF:Artist", "EXIF:XPAuthor", "XMP:Creator", "IPTC:By-line"],
    "DateTaken":   ["EXIF:DateTimeOriginal", "EXIF:DateTimeDigitized", "XMP:DateCreated"],
    "ProgramName": ["EXIF:Software", "XMP:CreatorTool"],
    "DateAcquired":["XMP:MetadataDate"],
    "Copyright":   ["EXIF:Copyright", "XMP:Rights", "IPTC:CopyrightNotice"],
    # GPS (decimal degrees)
    "GPSLatitude": ["EXIF:GPSLatitude"],
    "GPSLongitude":["EXIF:GPSLongitude"],
    "GPSAltitude": ["EXIF:GPSAltitude"],
}

# Fields which are array-like (keywords)
ARRAY_FIELDS = {"Tags", "Subject"}


# ── subprocess helper ─────────────────────────────────────────────────────────

def _run(cmd: List[str]) -> Tuple[int, str, str]:
    """Run a subprocess, suppressing any console window on Windows."""
    kwargs: dict = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
    }
    # Prevent a black console window from flashing on Windows frozen builds
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW  # = 0x08000000
    try:
        proc = subprocess.run(cmd, **kwargs)
        return proc.returncode, proc.stdout, proc.stderr
    except OSError as e:
        # e.g. [WinError 193] %1 is not a valid Win32 application
        return 1, "", str(e)


# ── ExifTool path resolution ──────────────────────────────────────────────────

def _bundled_exiftool_path() -> str:
    """Return path to bundled exiftool if running from a frozen app (PyInstaller).

    The spec bundles the tool to 'leosetter/tools', so inside the frozen bundle
    it lives at:  <_MEIPASS>/leosetter/tools/exiftool.exe
    """
    base = getattr(sys, "_MEIPASS", None)
    if base:
        # spec places it under leosetter/tools/ inside _MEIPASS
        cand_win = os.path.join(base, "leosetter", "tools", "exiftool.exe")
        cand_lin = os.path.join(base, "leosetter", "tools", "exiftool")
        if os.path.isfile(cand_win):
            return cand_win
        if os.path.isfile(cand_lin):
            return cand_lin

    # Development fallback: resolve relative to this source file
    here = os.path.dirname(os.path.abspath(__file__))
    cand_rel_win = os.path.join(here, "tools", "exiftool.exe")
    cand_rel     = os.path.join(here, "tools", "exiftool")
    if sys.platform == "win32":
        if os.path.isfile(cand_rel_win):
            return cand_rel_win
        if os.path.isfile(cand_rel):
            return cand_rel
    else:
        if os.path.isfile(cand_rel):
            return cand_rel
        if os.path.isfile(cand_rel_win):
            return cand_rel_win
    return ""


def _exiftool_cmd() -> str:
    """Resolve the exiftool command path, preferring bundled binary if present."""
    bundled = _bundled_exiftool_path()
    if bundled:
        return bundled
    return "exiftool"


def ensure_exiftool_available() -> bool:
    cmd = _exiftool_cmd()
    rc, _, _ = _run([cmd, "-ver"])
    return rc == 0


# ── Read / Write ──────────────────────────────────────────────────────────────

def read_metadata(path: str) -> Dict[str, str]:
    """Read a subset of tags from an image using exiftool.
    Returns a flat dict of our UI fields.
    """
    cmd = (
        [_exiftool_cmd(), "-n", "-s", "-s", "-s", "-json"]
        + [f"-{t}" for t in sorted({t for lst in TAG_MAP.values() for t in lst})]
        + [path]
    )
    rc, out, err = _run(cmd)

    if rc != 0:
        if not ensure_exiftool_available():
            logger.error("ExifTool is not installed or runnable.")
            raise RuntimeError(
                f"exiftool is not installed or runnable. "
                f"Path resolved to: '{_exiftool_cmd()}'. Error: {err.strip()}"
            )
        logger.error(f"ExifTool read failed for {path}: {err.strip()}")
        raise RuntimeError(f"exiftool read failed: {err.strip()}")
    try:
        data = json.loads(out)[0]
    except Exception as e:
        logger.exception(f"Failed parsing ExifTool JSON output for {path}. Output: {out[:200]}")
        raise RuntimeError(f"Failed parsing exiftool JSON: {e}")

    result: Dict[str, str] = {}
    for field, tag_list in TAG_MAP.items():
        val = None
        for tag in tag_list:
            key = tag.split(":", 1)[-1]  # strip group prefix
            if key in data:
                val = data[key]
                break
        if val is None:
            continue
        if field in ARRAY_FIELDS and isinstance(val, list):
            result[field] = ", ".join(str(x) for x in val)
        else:
            result[field] = str(val)
    return result


def parse_decimal_or_dms(val: str) -> float:
    try:
        return float(val)
    except ValueError:
        pass
    match = re.search(
        r"""(?:(?P<dir_front>[NSEW])\s*)?(?P<deg>-?\d+(?:\.\d+)?)\s*[°d]?\s*"""
        r"""(?:(?P<min>\d+(?:\.\d+)?)\s*['m]?\s*)?(?:(?P<sec>\d+(?:\.\d+)?)\s*["s]?\s*)?"""
        r"""(?P<dir_back>[NSEW])?""",
        val,
        re.IGNORECASE,
    )
    if not match:
        raise ValueError(f"Could not parse coordinate: {val}")

    deg     = float(match.group("deg") or 0)
    minutes = float(match.group("min") or 0)
    sec     = float(match.group("sec") or 0)

    decimal = abs(deg) + minutes / 60.0 + sec / 3600.0
    if deg < 0:
        decimal = -decimal

    direction = (match.group("dir_front") or match.group("dir_back") or "").upper()
    if direction in ["S", "W"]:
        decimal = -decimal

    return decimal


def _tag_assignments(payload: Dict[str, str], skip_keywords: bool = False) -> List[str]:
    args: List[str] = []

    gps_fields = ["GPSLatitude", "GPSLongitude", "GPSAltitude"]
    for g in gps_fields:
        if g in payload:
            val = payload[g]
            if val == "":
                args.append(f"-EXIF:{g}=")
                args.append(f"-EXIF:{g}Ref=")
            else:
                try:
                    num = parse_decimal_or_dms(val)
                    if g == "GPSLatitude":
                        ref = "N" if num >= 0 else "S"
                    elif g == "GPSLongitude":
                        ref = "E" if num >= 0 else "W"
                    else:
                        ref = 0 if num >= 0 else 1
                    args.append(f"-EXIF:{g}={abs(num)}")
                    args.append(f"-EXIF:{g}Ref={ref}")
                except ValueError:
                    continue

    for field, value in payload.items():
        if field in gps_fields:
            continue
        if skip_keywords and field == "Tags":
            continue
        tags = TAG_MAP.get(field)
        if not tags:
            continue
        is_empty = value.strip() == ""
        target_tags = tags
        if is_empty:
            for tag in target_tags:
                args.append(f"-{tag}=")
        else:
            if field in ARRAY_FIELDS:
                parts = [v.strip() for v in value.split(",") if v.strip()]
                for tag in target_tags:
                    if not parts:
                        args.append(f"-{tag}=")
                    else:
                        args.append(f"-{tag}={', '.join(parts)}")
            else:
                for tag in target_tags:
                    args.append(f"-{tag}={value}")
    return args


def _create_backups(paths) -> None:
    path_list = [paths] if isinstance(paths, str) else paths
    for p in path_list:
        if not os.path.exists(p):
            continue
        folder = os.path.dirname(p)
        backup_dir = os.path.join(folder, "LeoSetter_Backups")
        os.makedirs(backup_dir, exist_ok=True)
        filename = os.path.basename(p)
        target_path = os.path.join(backup_dir, filename)
        if not os.path.exists(target_path):
            try:
                shutil.copy2(p, target_path)
                logger.info(f"Created backup for {filename} in {backup_dir}")
            except Exception as e:
                logger.error(f"Failed to backup {p}: {e}")


def write_metadata(paths, payload: Dict[str, str], skip_keywords: bool = False, inplace: bool = False) -> None:
    if not ensure_exiftool_available():
        raise RuntimeError("exiftool is not installed.")
    if not inplace:
        _create_backups(paths)
    args = [_exiftool_cmd(), "-n", "-overwrite_original"]
    args += _tag_assignments(payload, skip_keywords=skip_keywords)
    if isinstance(paths, str):
        args.append(paths)
    else:
        args.extend(paths)
    rc, _, err = _run(args)
    if rc != 0:
        logger.error(f"ExifTool write failed. Error: {err.strip()}")
        raise RuntimeError(f"exiftool write failed: {err.strip()}")


def clear_metadata(paths, fields: List[str], inplace: bool = False) -> None:
    if not ensure_exiftool_available():
        raise RuntimeError("exiftool is not installed.")
    if not inplace:
        _create_backups(paths)
    args = [_exiftool_cmd(), "-overwrite_original"]
    for field in fields:
        tags = TAG_MAP.get(field, [])
        if not tags:
            continue
        for tag in tags:
            args.append(f"-{tag}=")
        if field == "GPSLatitude":
            args.append("-EXIF:GPSLatitudeRef=")
        elif field == "GPSLongitude":
            args.append("-EXIF:GPSLongitudeRef=")
        elif field == "GPSAltitude":
            args.append("-EXIF:GPSAltitudeRef=")
    if isinstance(paths, str):
        args.append(paths)
    else:
        args.extend(paths)
    rc, _, err = _run(args)
    if rc != 0:
        logger.error(f"ExifTool clear failed. Error: {err.strip()}")
        raise RuntimeError(f"exiftool clear failed: {err.strip()}")


def batch_apply(paths: List[str], payload: Dict[str, str], skip_keywords: bool = False, inplace: bool = False) -> None:
    for p in paths:
        write_metadata(p, payload, skip_keywords=skip_keywords, inplace=inplace)


def batch_clear(paths: List[str], fields: List[str], inplace: bool = False) -> None:
    for p in paths:
        clear_metadata(p, fields, inplace=inplace)


def read_raw_json(path: str) -> str:
    """Return full exiftool JSON for a given file (read-only viewing)."""
    if not ensure_exiftool_available():
        raise RuntimeError("exiftool is not installed.")
    rc, out, err = _run([_exiftool_cmd(), "-G1", "-a", "-json", path])
    if rc != 0:
        raise RuntimeError(f"exiftool raw read failed: {err.strip()}")
    try:
        data = json.loads(out)
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception:
        return out
