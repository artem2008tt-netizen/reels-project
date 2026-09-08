#!/usr/bin/env python3
"""Search the Pexels Video API for B-roll candidates.

Reads PEXELS_API_KEY from the environment, falling back to a
PEXELS_API_KEY=... line in ~/Developer/video-use/.env (same convention
this project already uses for ELEVENLABS_API_KEY). The key is never
printed, logged, or written anywhere by this script.

Usage:
    python3 pexels_search.py "woman using smartphone in cafe" --per-page 3
    python3 pexels_search.py "team meeting" --orientation portrait --per-page 5
"""
import argparse
import json
import os
import sys
from pathlib import Path

import requests

ENV_FILE = Path.home() / "Developer" / "video-use" / ".env"
API_URL = "https://api.pexels.com/videos/search"


def load_key() -> str | None:
    key = os.environ.get("PEXELS_API_KEY")
    if key:
        return key
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if line.startswith("PEXELS_API_KEY="):
                return line.split("=", 1)[1].strip()
    return None


def search(query: str, per_page: int = 5, orientation: str = "portrait") -> dict:
    key = load_key()
    if not key:
        sys.exit(
            "PEXELS_API_KEY not set. Export it or add "
            f"PEXELS_API_KEY=... to {ENV_FILE}"
        )
    resp = requests.get(
        API_URL,
        headers={"Authorization": key},
        params={"query": query, "per_page": per_page, "orientation": orientation},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()


def summarize(data: dict) -> list[dict]:
    out = []
    for v in data.get("videos", []):
        files = sorted(
            v.get("video_files", []), key=lambda f: (f.get("height") or 0), reverse=True
        )
        best = files[0] if files else {}
        out.append(
            {
                "id": v["id"],
                "pexels_url": v["url"],
                "duration_s": v.get("duration"),
                "width": v.get("width"),
                "height": v.get("height"),
                "author": (v.get("user") or {}).get("name"),
                "best_file": {
                    "quality": best.get("quality"),
                    "width": best.get("width"),
                    "height": best.get("height"),
                    "link": best.get("link"),
                },
            }
        )
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("query")
    ap.add_argument("--per-page", type=int, default=5)
    ap.add_argument(
        "--orientation", default="portrait", choices=["portrait", "landscape", "square"]
    )
    args = ap.parse_args()

    data = search(args.query, args.per_page, args.orientation)
    print(json.dumps(summarize(data), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
