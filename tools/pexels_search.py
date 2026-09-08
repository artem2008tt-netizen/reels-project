#!/usr/bin/env python3
"""Search the official Pexels Video API for B-roll candidates.

ENDPOINT
    GET https://api.pexels.com/videos/search
    Pexels' Video API has no /v1/ prefix -- /v1/ is only used by the
    Photos API (/v1/search). Videos live at /videos/search.

AUTH
    Header: Authorization: <raw key> (no "Bearer" prefix).
    Reads PEXELS_API_KEY from the environment first. If unset, falls
    back to a PEXELS_API_KEY=... line in a .env file, checked in this
    order:
      1. .env next to this script (convenient for a local Windows checkout)
      2. ~/Developer/video-use/.env (this project's cloud/video-use convention)
    The key is never printed, logged, or written anywhere by this script.

DEPENDENCIES
    None beyond the Python 3 standard library (urllib) -- nothing to
    pip install before running this on a fresh Windows machine.

USAGE
    python pexels_search.py "woman using smartphone in cafe" --count 3
    python pexels_search.py "team meeting" --orientation portrait --count 5

PowerShell (Windows), setting the key for this session only:
    $env:PEXELS_API_KEY = "<your key>"
    python pexels_search.py "woman using smartphone in cafe" --orientation portrait --count 3
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API_URL = "https://api.pexels.com/videos/search"
SCRIPT_DIR = Path(__file__).resolve().parent
CANDIDATE_ENV_FILES = [
    SCRIPT_DIR / ".env",
    Path.home() / "Developer" / "video-use" / ".env",
]
TARGET_ASPECT = 9 / 16  # Reels vertical target


def load_key():
    key = os.environ.get("PEXELS_API_KEY")
    if key:
        return key
    for env_file in CANDIDATE_ENV_FILES:
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("PEXELS_API_KEY="):
                    return line.split("=", 1)[1].strip()
    return None


def search(query: str, count: int, orientation: str) -> dict:
    key = load_key()
    if not key:
        sys.exit(
            "PEXELS_API_KEY not set.\n"
            'PowerShell:  $env:PEXELS_API_KEY = "<your key>"\n'
            f"or add a PEXELS_API_KEY=... line to one of:\n  "
            + "\n  ".join(str(p) for p in CANDIDATE_ENV_FILES)
        )
    qs = urllib.parse.urlencode(
        {"query": query, "per_page": count, "orientation": orientation}
    )
    req = urllib.request.Request(
        f"{API_URL}?{qs}",
        headers={"Authorization": key},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        sys.exit(f"Pexels API returned HTTP {e.code}: {body[:300]}")
    except urllib.error.URLError as e:
        sys.exit(
            f"Could not reach {API_URL} ({e.reason}). "
            "If this is a network/proxy block, that's environment-level -- "
            "not a code or key problem."
        )


def best_portrait_file(video: dict) -> dict:
    files = video.get("video_files", [])
    portrait = [f for f in files if (f.get("height") or 0) >= (f.get("width") or 0)]
    pool = portrait or files
    pool = sorted(pool, key=lambda f: (f.get("height") or 0), reverse=True)
    return pool[0] if pool else {}


def summarize(data: dict) -> list:
    out = []
    for v in data.get("videos", []):
        w, h = v.get("width") or 0, v.get("height") or 0
        ratio = round(w / h, 4) if h else None
        best = best_portrait_file(v)
        slug = (v.get("url") or "").rstrip("/").rsplit("/", 1)[-1]
        out.append(
            {
                "video_id": v.get("id"),
                "pexels_url": v.get("url"),
                "photographer": (v.get("user") or {}).get("name"),
                "duration_s": v.get("duration"),
                "width": w,
                "height": h,
                "aspect_ratio": ratio,
                "closeness_to_9x16": round(abs((ratio or 0) - TARGET_ASPECT), 4)
                if ratio
                else None,
                "download_url": best.get("link"),
                "download_resolution": (
                    f"{best.get('width')}x{best.get('height')}"
                    if best.get("width")
                    else None
                ),
                # Pexels' Video API has no caption/description field.
                # This is just the URL slug Pexels itself generates for the
                # page -- real Pexels data, but not a real "description".
                "pexels_url_slug": slug,
            }
        )
    return out


def main():
    ap = argparse.ArgumentParser(
        description="Search Pexels Video API for B-roll.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("query", help="Search query")
    ap.add_argument("--count", type=int, default=3, help="Number of results (default 3)")
    ap.add_argument(
        "--orientation",
        default="portrait",
        choices=["portrait", "landscape", "square"],
        help="Pexels orientation filter (default portrait)",
    )
    args = ap.parse_args()

    data = search(args.query, args.count, args.orientation)
    print(json.dumps(summarize(data), indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
