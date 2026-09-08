#!/usr/bin/env python3
"""Pexels B-roll automation module.

Given a list of (kind, query) slots -- decided by Claude when reading a
Reels script and deciding where extra photo/video coverage is needed,
not by this module -- this searches Pexels, picks the best portrait
candidate per slot, downloads it, crops it to an exact 1080x1920 (9:16)
frame with ffmpeg, and writes a metadata JSON record next to it.

OUTPUT STRUCTURE (relative to --out, default assets/pexels)
    photos/<slug>.jpg
    videos/<slug>.mp4
    metadata/<slug>.json

ENDPOINTS
    Photos: GET https://api.pexels.com/v1/search
    Videos: GET https://api.pexels.com/videos/search
    (Photos API uses /v1/, Videos API does not -- see pexels_search.py
    for the reasoning; mixing them up gives a 404, not a network error.)

AUTH
    Header: Authorization: <raw PEXELS_API_KEY> (no "Bearer" prefix).
    Key is loaded by pexels_common.require_key() -- env var first, then
    a local .env. Never printed, logged, or written anywhere here.

CROP STRATEGY
    Target is always exactly 1080x1920. ffmpeg's
        scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920
    scales the source to COVER the frame (no black bars), then center-
    crops to the exact target. This is the same filter for photos and
    videos, and for portrait or landscape sources alike -- a landscape
    video that had no vertical candidate still lands at exactly 9:16.
    Video is re-encoded with libx264; audio is dropped (-an) since
    B-roll is composited silently under the main edit's audio in
    video-use -- it is not meant to carry its own sound.

SELECTION
    Each slot fetches CANDIDATES_PER_SLOT (3) results from Pexels and
    keeps the one closest to the 9:16 target aspect ratio. Only that
    one candidate is downloaded -- the other two are discarded without
    ever being fetched.

DEPENDENCIES
    Python 3 stdlib (urllib) + ffmpeg/ffprobe on PATH. No pip installs.

CLI
    python pexels_broll.py \\
        --photo "confident businesswoman using smartphone modern office" \\
        --photo "young professional team mentoring discussion office" \\
        --video "businesswoman talking explaining gesture office natural" \\
        --video "team collaboration meeting modern office candid" \\
        --out assets/pexels

    Repeat --photo/--video for as many slots as the script needs.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pexels_common import require_key  # noqa: E402

PHOTO_API = "https://api.pexels.com/v1/search"
VIDEO_API = "https://api.pexels.com/videos/search"
CANDIDATES_PER_SLOT = 3
TARGET_W, TARGET_H = 1080, 1920
TARGET_ASPECT = TARGET_W / TARGET_H
CROP_FILTER = (
    f"scale={TARGET_W}:{TARGET_H}:force_original_aspect_ratio=increase,"
    f"crop={TARGET_W}:{TARGET_H}"
)


def _get(url: str, params: dict, key: str) -> dict:
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{url}?{qs}", headers={"Authorization": key})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        sys.exit(f"Pexels API HTTP {e.code} for {url}: {body[:300]}")
    except urllib.error.URLError as e:
        sys.exit(
            f"Could not reach {url} ({e.reason}). "
            "Network/proxy block, not a code or key problem."
        )


def search_photos(query: str, key: str, count: int = CANDIDATES_PER_SLOT) -> list:
    data = _get(
        PHOTO_API, {"query": query, "per_page": count, "orientation": "portrait"}, key
    )
    photos = data.get("photos", [])
    if photos:
        return photos
    data = _get(PHOTO_API, {"query": query, "per_page": count}, key)
    return data.get("photos", [])


def search_videos(query: str, key: str, count: int = CANDIDATES_PER_SLOT) -> list:
    data = _get(
        VIDEO_API, {"query": query, "per_page": count, "orientation": "portrait"}, key
    )
    videos = data.get("videos", [])
    if videos:
        return videos
    # No portrait candidate exists for this query -- widen to landscape.
    # The crop step below still forces the final file to exactly 9:16.
    data = _get(
        VIDEO_API, {"query": query, "per_page": count, "orientation": "landscape"}, key
    )
    return data.get("videos", [])


def _closeness(w, h) -> float:
    return abs((w / h if h else 0) - TARGET_ASPECT)


def pick_best_photo(candidates: list):
    if not candidates:
        return None
    return min(candidates, key=lambda p: _closeness(p.get("width", 0), p.get("height", 0)))


def pick_best_video(candidates: list):
    if not candidates:
        return None
    return min(candidates, key=lambda v: _closeness(v.get("width", 0), v.get("height", 0)))


def _slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:60] or "asset"


def _rel_or_abs(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(
        url, headers={"User-Agent": "reels-project-pexels-broll/1.0"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as f:
        f.write(resp.read())


def crop_image_to_9x16(src: Path, dst: Path) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error", "-i", str(src),
            "-vf", CROP_FILTER, "-frames:v", "1", str(dst),
        ],
        check=True,
    )


def crop_video_to_9x16(src: Path, dst: Path) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error", "-i", str(src),
            "-vf", CROP_FILTER, "-an",
            "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
            str(dst),
        ],
        check=True,
    )


def probe(path: Path) -> dict:
    out = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-show_entries", "format=duration",
            "-of", "json", str(path),
        ],
        check=True, capture_output=True, text=True,
    )
    data = json.loads(out.stdout)
    stream = (data.get("streams") or [{}])[0]
    fmt = data.get("format") or {}
    return {
        "width": stream.get("width"),
        "height": stream.get("height"),
        "duration_s": float(fmt["duration"]) if "duration" in fmt else None,
    }


def process_photo(query: str, key: str, out_root: Path) -> dict:
    candidates = search_photos(query, key)
    best = pick_best_photo(candidates)
    if not best:
        return {"kind": "photo", "search_query": query, "error": "no candidates found"}

    slug = f"{_slugify(query)}-{best['id']}"
    original_url = best["src"]["original"]
    suffix = Path(urllib.parse.urlparse(original_url).path).suffix or ".jpg"
    raw_path = out_root / "photos" / f"{slug}_raw{suffix}"
    final_path = out_root / "photos" / f"{slug}.jpg"

    download(original_url, raw_path)
    crop_image_to_9x16(raw_path, final_path)
    raw_path.unlink(missing_ok=True)
    dims = probe(final_path)

    record = {
        "kind": "photo",
        "search_query": query,
        "pexels_id": best["id"],
        "pexels_url": best.get("url"),
        "photographer": best.get("photographer"),
        "original_url": original_url,
        "local_file": _rel_or_abs(final_path),
        "width": dims["width"],
        "height": dims["height"],
        "aspect_ratio": round(dims["width"] / dims["height"], 4) if dims["height"] else None,
        "is_9x16": dims["width"] == TARGET_W and dims["height"] == TARGET_H,
    }
    (out_root / "metadata" / f"{slug}.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=True), encoding="utf-8"
    )
    return record


def process_video(query: str, key: str, out_root: Path) -> dict:
    candidates = search_videos(query, key)
    best = pick_best_video(candidates)
    if not best:
        return {"kind": "video", "search_query": query, "error": "no candidates found"}

    files = sorted(
        best.get("video_files", []), key=lambda f: (f.get("height") or 0), reverse=True
    )
    src_file = files[0] if files else None
    if not src_file:
        return {
            "kind": "video", "search_query": query,
            "error": "best candidate has no downloadable file",
        }

    slug = f"{_slugify(query)}-{best['id']}"
    raw_path = out_root / "videos" / f"{slug}_raw.mp4"
    final_path = out_root / "videos" / f"{slug}.mp4"

    download(src_file["link"], raw_path)
    crop_video_to_9x16(raw_path, final_path)
    raw_path.unlink(missing_ok=True)
    dims = probe(final_path)

    record = {
        "kind": "video",
        "search_query": query,
        "pexels_id": best["id"],
        "pexels_url": best.get("url"),
        "photographer": (best.get("user") or {}).get("name"),
        "original_url": src_file["link"],
        "local_file": _rel_or_abs(final_path),
        "width": dims["width"],
        "height": dims["height"],
        "aspect_ratio": round(dims["width"] / dims["height"], 4) if dims["height"] else None,
        "duration_s": dims["duration_s"],
        "is_9x16": dims["width"] == TARGET_W and dims["height"] == TARGET_H,
    }
    (out_root / "metadata" / f"{slug}.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=True), encoding="utf-8"
    )
    return record


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--photo", action="append", default=[], metavar="QUERY",
        help="English search query for a photo slot (repeatable)",
    )
    ap.add_argument(
        "--video", action="append", default=[], metavar="QUERY",
        help="English search query for a video slot (repeatable)",
    )
    ap.add_argument("--out", default="assets/pexels", help="Output root (default assets/pexels)")
    args = ap.parse_args()

    if not args.photo and not args.video:
        sys.exit("Nothing to do -- pass at least one --photo or --video query.")

    key = require_key()
    out_root = Path(args.out).resolve()
    for sub in ("photos", "videos", "metadata"):
        (out_root / sub).mkdir(parents=True, exist_ok=True)

    results = []
    for q in args.photo:
        results.append(process_photo(q, key, out_root))
    for q in args.video:
        results.append(process_video(q, key, out_root))

    print(json.dumps(results, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
