"""Shared helpers for the Pexels tools in this project.

Not a Pexels client itself -- just the key-loading logic that both
pexels_search.py (quick manual test) and pexels_broll.py (the
automation module) need, kept in exactly one place.

Reads PEXELS_API_KEY from the environment first. If unset, falls back
to a PEXELS_API_KEY=... line in a .env file, checked in this order:
  1. .env next to these scripts (convenient for a local checkout)
  2. ~/Developer/video-use/.env (this project's cloud/video-use convention)
The key is never printed, logged, or written anywhere by this module.
"""
import os
import sys
from pathlib import Path

CANDIDATE_ENV_FILES = [
    Path(__file__).resolve().parent / ".env",
    Path.home() / "Developer" / "video-use" / ".env",
]


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


def require_key() -> str:
    key = load_key()
    if not key:
        sys.exit(
            "PEXELS_API_KEY not set.\n"
            'PowerShell:  $env:PEXELS_API_KEY = "<your key>"\n'
            "or add a PEXELS_API_KEY=... line to one of:\n  "
            + "\n  ".join(str(p) for p in CANDIDATE_ENV_FILES)
        )
    return key
