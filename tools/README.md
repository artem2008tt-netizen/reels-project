# Pexels B-roll tools

Two scripts, one shared key-loader. Both are pure Python 3 stdlib +
`ffmpeg`/`ffprobe` on PATH -- nothing to `pip install`.

- **`pexels_common.py`** -- shared `require_key()` / `load_key()`. Not run
  directly.
- **`pexels_search.py`** -- quick manual lookup against the Pexels Video
  API. Prints candidate metadata (no download). Good for eyeballing
  results before committing to a query.
- **`pexels_broll.py`** -- the automation module. For each `--photo`/
  `--video` query it searches Pexels, picks the candidate closest to a
  9:16 aspect ratio, downloads only that one, crops it to an exact
  1080x1920 frame with `ffmpeg`, and writes a metadata JSON record.

## API key

Every script reads `PEXELS_API_KEY`, in this order:

1. The environment variable itself.
2. A `PEXELS_API_KEY=...` line in a `.env` file next to these scripts
   (`tools/.env` -- gitignored).
3. A `PEXELS_API_KEY=...` line in `~/Developer/video-use/.env` (the
   cloud video-use setup's own key file, reused for convenience there).

The key is never printed, logged, hardcoded, or written to any file by
these scripts. Get a key at <https://www.pexels.com/api/>.

PowerShell, setting it for the current session only:

```powershell
$env:PEXELS_API_KEY = "<your key>"
```

## `pexels_search.py` -- quick lookup

```bash
python tools/pexels_search.py "woman using smartphone in cafe" --orientation portrait --count 3
```

Prints JSON with `video_id`, `pexels_url`, `photographer`, `duration_s`,
`width`/`height`, `aspect_ratio`, `download_url`. Nothing is downloaded.

## `pexels_broll.py` -- search, download, crop, record

```bash
python tools/pexels_broll.py \
  --photo "confident businesswoman using smartphone modern office" \
  --photo "young professional team mentoring discussion office" \
  --video "businesswoman talking explaining gesture office natural" \
  --video "team collaboration meeting modern office candid" \
  --out assets/pexels
```

Each `--photo`/`--video` is one English search query for one B-roll
slot -- Claude decides the queries when reading a Reels script and
deciding where extra coverage helps; the script only executes them.
Repeat the flag for as many slots as needed.

For every slot: fetch 3 candidates, keep the one closest to 9:16,
download **only** that one, crop it to exactly 1080x1920 with ffmpeg
(cover-then-center-crop -- no black bars, works for portrait or
landscape sources alike), and write a metadata record.

### Output

```
assets/pexels/
├── photos/<slug>.jpg          # final, already 1080x1920
├── videos/<slug>.mp4          # final, already 1080x1920, no audio
└── metadata/<slug>.json       # one record per asset, see below
```

Video B-roll ships with `-an` (audio stripped) since it is composited
silently under the main edit's audio track in video-use -- it isn't
meant to carry its own sound.

### Metadata record

```json
{
  "kind": "video",
  "search_query": "businesswoman talking explaining gesture office natural",
  "pexels_id": 1234567,
  "pexels_url": "https://www.pexels.com/video/...-1234567/",
  "photographer": "Name",
  "original_url": "https://videos.pexels.com/video-files/.../....mp4",
  "local_file": "assets/pexels/videos/businesswoman-talking-...-1234567.mp4",
  "width": 1080,
  "height": 1920,
  "aspect_ratio": 0.5625,
  "duration_s": 8.2,
  "is_9x16": true
}
```

`is_9x16` is a real post-crop `ffprobe` check on the output file, not
an assumption -- it's `false` if the crop step ever produced something
off-target.

## Feeding results into video-use

No architecture change: a cropped B-roll file in `assets/pexels/` is an
ordinary video/image file. To use one in a cut, point an `edl.json`
`source`/overlay entry at its `local_file` path -- `render.py` doesn't
need to know where the file came from.
