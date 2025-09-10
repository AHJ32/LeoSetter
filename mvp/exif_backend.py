import json
import os
import shlex
import subprocess
import sys
from typing import Dict, List, Tuple

# Mapping from our UI field names to exiftool tag names (prefer XMP where sane)
TAG_MAP = {
    # Description
    "Title": ["EXIF:XPTitle", "XMP:Title", "IPTC:ObjectName", "EXIF:ImageDescription"],
    # Use Headline/ObjectName for a short subject line; avoid XMP:Subject (keywords)
    "Subject": ["EXIF:XPSubject", "XMP:Headline", "IPTC:ObjectName"],
    "Rating": ["XMP:Rating"],
    "Tags": ["EXIF:XPKeywords", "XMP:TagsList", "XMP:Subject", "IPTC:Keywords"],  # Keywords
    "Comments": ["EXIF:XPComment", "XMP:Description", "EXIF:UserComment", "IPTC:Caption-Abstract"],
    # Origin
    "Authors": ["XMP:Creator", "IPTC:By-line"],
    "DateTaken": ["EXIF:DateTimeOriginal", "XMP:DateCreated"],
    "ProgramName": ["XMP:CreatorTool"],
    "DateAcquired": ["XMP:MetadataDate"],
    "Copyright": ["XMP:Rights", "EXIF:Copyright"],
    # GPS (decimal degrees)
    "GPSLatitude": ["EXIF:GPSLatitude"],
    "GPSLongitude": ["EXIF:GPSLongitude"],
    "GPSAltitude": ["EXIF:GPSAltitude"],
}

# Fields which are array-like (keywords)
ARRAY_FIELDS = {"Tags", "Subject"}


def _run(cmd: List[str]) -> Tuple[int, str, str]:
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def _bundled_exiftool_path() -> str:
    """Return path to bundled exiftool if running from a frozen app (PyInstaller).

    On Windows builds we may ship tools/exiftool.exe inside the bundle.
    On Linux we may ship tools/exiftool (optional).
    """
    # PyInstaller sets sys.frozen and provides sys._MEIPASS for data files
    base = getattr(sys, "_MEIPASS", None)
    if base:
        # try Windows naming first, then Linux
        cand_win = os.path.join(base, "tools", "exiftool.exe")
        cand_lin = os.path.join(base, "tools", "exiftool")
        if os.path.isfile(cand_win):
            return cand_win
        if os.path.isfile(cand_lin):
            return cand_lin
    # Also try a relative tools/ folder next to this file (useful for dev builds)
    here = os.path.dirname(__file__)
    cand_rel = os.path.join(here, "tools", "exiftool")
    if os.path.isfile(cand_rel):
        return cand_rel
    cand_rel_win = os.path.join(here, "tools", "exiftool.exe")
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
    # Try to execute `exiftool -ver` to ensure it is runnable
    rc, _, _ = _run([cmd, "-ver"])  # type: ignore
    return rc == 0


def read_metadata(path: str) -> Dict[str, str]:
    """Read a subset of tags from an image using exiftool.
    Returns a flat dict of our UI fields.
    """
    if not ensure_exiftool_available():
        raise RuntimeError("exiftool is not installed. Please install it (e.g., sudo apt install exiftool)")
    # Build exiftool arg list for all mapped tags
    tags = sorted({t for lst in TAG_MAP.values() for t in lst})
    # -n for numeric output (GPS, rating, etc.)
    cmd = [_exiftool_cmd(), "-n", "-s", "-s", "-s", "-json"] + [f"-{t}" for t in tags] + [path]
    rc, out, err = _run(cmd)
    if rc != 0:
        raise RuntimeError(f"exiftool read failed: {err.strip()}")
    try:
        data = json.loads(out)[0]
    except Exception as e:
        raise RuntimeError(f"Failed parsing exiftool JSON: {e}")

    result: Dict[str, str] = {}
    for field, tag_list in TAG_MAP.items():
        val = None
        for tag in tag_list:
            key = tag.split(":", 1)[-1]  # exiftool json keys are sans group by default with -s -s -s
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


def _tag_assignments(payload: Dict[str, str], skip_keywords: bool = False) -> List[str]:
    args: List[str] = []
    # GPS handling: ensure Ref and numeric values
    lat = payload.get("GPSLatitude")
    lon = payload.get("GPSLongitude")
    alt = payload.get("GPSAltitude")
    def _is_num(v: str | None) -> bool:
        if v is None:
            return False
        try:
            float(v)
            return True
        except Exception:
            return False
    if _is_num(lat):
        v = float(lat)  # type: ignore
        ref = "N" if v >= 0 else "S"
        args.append(f"-EXIF:GPSLatitudeRef={ref}")
        args.append(f"-EXIF:GPSLatitude={abs(v)}")
    if _is_num(lon):
        v = float(lon)  # type: ignore
        ref = "E" if v >= 0 else "W"
        args.append(f"-EXIF:GPSLongitudeRef={ref}")
        args.append(f"-EXIF:GPSLongitude={abs(v)}")
    if _is_num(alt):
        v = float(alt)  # type: ignore
        # AltitudeRef: 0 = Above sea level, 1 = Below sea level
        ref = 0 if v >= 0 else 1
        args.append(f"-EXIF:GPSAltitudeRef={ref}")
        args.append(f"-EXIF:GPSAltitude={abs(v)}")
    for field, value in payload.items():
        if skip_keywords and field == "Tags":
            continue
        tags = TAG_MAP.get(field)
        if not tags:
            continue
        # For Windows-visible fields, write to all mapped tags; otherwise first only
        write_all = field in ("Title", "Subject", "Comments", "Tags")
        target_tags = tags if write_all else [tags[0]]
        # Normalize arrays
        if field in ARRAY_FIELDS:
            parts = [v.strip() for v in (value or "").split(",") if v.strip()]
            for tag in target_tags:
                if not parts:
                    args.append(f"-{tag}=")
                elif tag.endswith("XPKeywords"):
                    # Windows expects semicolon-separated keywords
                    args.append(f"-{tag}={'; '.join(parts)}")
                else:
                    for part in parts:
                        args.append(f"-{tag}={part}")
        else:
            for tag in target_tags:
                args.append(f"-{tag}={value}")
    return args


def write_metadata(path: str, payload: Dict[str, str], skip_keywords: bool = False, inplace: bool = False) -> None:
    if not ensure_exiftool_available():
        raise RuntimeError("exiftool is not installed.")
    # -n enforces numeric input where applicable (GPS, rating)
    args = [_exiftool_cmd(), "-n"]
    if inplace:
        args.append("-overwrite_original")
    else:
        # write to new file (exiftool will create filename_copy.ext by default)
        pass
    args += _tag_assignments(payload, skip_keywords=skip_keywords)
    args.append(path)
    rc, _, err = _run(args)
    if rc != 0:
        raise RuntimeError(f"exiftool write failed: {err.strip()}")


def clear_metadata(path: str, fields: List[str], inplace: bool = False) -> None:
    if not ensure_exiftool_available():
        raise RuntimeError("exiftool is not installed.")
    args = [_exiftool_cmd()]
    if inplace:
        args.append("-overwrite_original")
    for field in fields:
        tags = TAG_MAP.get(field, [])
        if not tags:
            continue
        # clear all mapped tags for this field
        for tag in tags:
            args.append(f"-{tag}=")
    args.append(path)
    rc, _, err = _run(args)
    if rc != 0:
        raise RuntimeError(f"exiftool clear failed: {err.strip()}")


def batch_apply(paths: List[str], payload: Dict[str, str], skip_keywords: bool = False, inplace: bool = False) -> None:
    for p in paths:
        write_metadata(p, payload, skip_keywords=skip_keywords, inplace=inplace)


def batch_clear(paths: List[str], fields: List[str], inplace: bool = False) -> None:
    for p in paths:
        clear_metadata(p, fields, inplace=inplace)


# Simple template storage in user config
BASE_DIR = os.path.dirname(__file__)
CONFIG_DIR = os.path.join(BASE_DIR, "templates")
TEMPLATES_FILE = os.path.join(CONFIG_DIR, "templates.json")


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


def read_raw_json(path: str) -> str:
    """Return full exiftool JSON for a given file (read-only viewing)."""
    if not ensure_exiftool_available():
        raise RuntimeError("exiftool is not installed.")
    # Use -G1 for groups, -a for duplicate tags, omit -s to keep full tag names
    rc, out, err = _run([_exiftool_cmd(), "-G1", "-a", "-json", path])
    if rc != 0:
        raise RuntimeError(f"exiftool raw read failed: {err.strip()}")
    try:
        data = json.loads(out)
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception as e:
        # If JSON parsing fails, still return raw output for visibility
        return out
