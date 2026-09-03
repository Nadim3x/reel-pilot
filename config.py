"""
ReelPilot — central configuration.

The whole stack is engineered around a 256 MB RAM budget on Fly.io
(shared-cpu-1x), so every default here is deliberately frugal:
tiny network buffers, single-threaded downloads, and explicit paths
that never assume more than one worker process.
"""

import os
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Python runtime memory guards (best-effort when set before interpreter
# arenas are allocated; harmless otherwise). These are also baked into the
# Dockerfile environment.
# ---------------------------------------------------------------------------
os.environ.setdefault("MALLOC_ARENA_MAX", "2")
os.environ.setdefault("PYTHONUNBUFFERED", "1")

# ---------------------------------------------------------------------------
# Persistent storage — Fly.io mounts the "bot_data" volume at /data.
# Locally (or when no volume exists) we fall back to the working directory.
# ---------------------------------------------------------------------------


def _pick_data_dir() -> Path:
    preferred = Path(os.getenv("REELPILOT_DATA_DIR", "/data"))
    try:
        preferred.mkdir(parents=True, exist_ok=True)
        probe = preferred / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return preferred
    except OSError:
        fallback = Path.cwd() / "bot_data_local"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


DATA_DIR: Path = _pick_data_dir()
DB_PATH: Path = DATA_DIR / "bot_data.db"
DOWNLOAD_DIR: Path = DATA_DIR / "downloads"
THUMB_PATH: Path = DATA_DIR / "global_custom_thumb.jpg"

DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Web dashboard
# ---------------------------------------------------------------------------
DASHBOARD_HOST: str = "0.0.0.0"
DASHBOARD_PORT: int = int(os.getenv("PORT", "8080"))

ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "nadim")
ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "N@dim69")

# Public URL of the dashboard, shown on the Telegram /start button.
WEBAPP_PUBLIC_URL: str = os.getenv("WEBAPP_PUBLIC_URL", f"http://localhost:{DASHBOARD_PORT}")

# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
SUPER_ADMIN_ID: int = int(os.getenv("SUPER_ADMIN_ID", "5668590673"))

# Random delay between posting to each account (seconds, inclusive).
ACCOUNT_DELAY_MIN: int = 3
ACCOUNT_DELAY_MAX: int = 7

# ---------------------------------------------------------------------------
# yt-dlp — memory-frugal profile.
#
# The downloader streams to disk chunk-by-chunk; a 16K network buffer and a
# 5 MB/s rate cap keep peak RSS and disk writes predictable inside the tiny
# shared-cpu-1x container. No browser extractors are used anywhere.
# ---------------------------------------------------------------------------
YDL_COMMON_OPTS: dict = {
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "noprogress": True,
    "socket_timeout": 30,
    "retries": 3,
    "concurrent_fragment_downloads": 1,
    "http_chunk_size": 16384,  # stream to disk in 16K chunks
    "ratelimit": 5 * 1024 * 1024,  # --limit-rate 5M
    "outtmpl": str(DOWNLOAD_DIR / "%(id)s.%(ext)s"),
    "restrictfilenames": True,
    "overwrites": True,
}

# Hard safety rails for the 256 MB container.
MAX_VIDEO_MB: int = 90        # refuse to fetch anything above this
MIN_FREE_DISK_MB: int = 120   # refuse to start a download below this

# ---------------------------------------------------------------------------
# Link detection
# ---------------------------------------------------------------------------
LINK_PATTERNS: dict = {
    "instagram": re.compile(r"https?://(?:www\.|m\.)?instagram\.com/\S+", re.IGNORECASE),
    "tiktok": re.compile(
        r"https?://(?:www\.|vm\.|vt\.|m\.)?tiktok\.com/\S+", re.IGNORECASE
    ),
    "facebook": re.compile(
        r"https?://(?:www\.|m\.|web\.)?facebook\.com/(?:watch/\S+|reel/\S+|[^/]+/videos/\S+)",
        re.IGNORECASE,
    ),
    "threads": re.compile(r"https?://(?:www\.)?threads\.(?:net|com)/\S+", re.IGNORECASE),
}


def detect_platform(text: str):
    """Return (platform, url) if *text* contains a supported media link."""
    for platform, pattern in LINK_PATTERNS.items():
        match = pattern.search(text)
        if match:
            return platform, match.group(0)
    return None, None


# ---------------------------------------------------------------------------
# Service root (static assets live next to this file)
# ---------------------------------------------------------------------------
APP_ROOT: Path = Path(__file__).resolve().parent
