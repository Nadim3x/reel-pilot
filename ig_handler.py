"""
ReelPilot — memory-efficient media pipeline.

Hard rules for the 256 MB container:
  * NO headless browsers. Nothing here imports selenium/playwright/etc.
  * yt-dlp streams to disk with a 16K chunk size and a 5 MB/s rate cap.
  * Every download/upload lifecycle ends with gc.collect() + temp cleanup.

Instagram posting goes through instagrapi (pure HTTP/JSON, no browser),
and TikTok uploads ride a Netscape-cookie session against the web upload
endpoints — both are featherweight HTTP paths.
"""

import gc
import json
import logging
import random
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import requests

import config
import database

logger = logging.getLogger(__name__)

ProgressFn = Callable[[str, str, float], None]  # (stage, detail, pct 0..1)


class DownloadError(Exception):
    """Raised when a link cannot be fetched (unsupported, too big, no space)."""


@dataclass
class VideoJob:
    url: str
    file_path: Path
    caption: str = ""
    ext: str = "mp4"


# ---------------------------------------------------------------------------
# Import guard: hard-block any browser-backed automation dependency.
# ---------------------------------------------------------------------------

_BANNED_MODULES = ("selenium", "playwright", "pyppeteer", "undetected_chromedriver")


class _BrowserBlocker:
    """A sys.meta_path finder that refuses to resolve browser engines."""

    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] in _BANNED_MODULES:
            raise ImportError(
                f"ReelPilot: '{name}' is blocked by the 256MB memory budget "
                "(no headless browsers allowed)."
            )
        return None


def _install_import_guard() -> None:
    import sys

    for mod in list(sys.modules):
        if mod.split(".")[0] in _BANNED_MODULES:
            del sys.modules[mod]
    blocker = _BrowserBlocker()
    blocker.__name__ = "ReelPilotBrowserBlocker"
    sys.meta_path.insert(0, blocker)


_install_import_guard()

# ---------------------------------------------------------------------------
# Disk / size guards
# ---------------------------------------------------------------------------

def disk_free_mb() -> float:
    usage = shutil.disk_usage(str(config.DATA_DIR))
    return usage.free / (1024 * 1024)


def disk_used_pct() -> float:
    usage = shutil.disk_usage(str(config.DATA_DIR))
    return round((usage.used / usage.total) * 100, 1)


def _ensure_download_space() -> None:
    if disk_free_mb() < config.MIN_FREE_DISK_MB:
        raise DownloadError(
            f"Low disk: {disk_free_mb():.0f}MB free, "
            f"{config.MIN_FREE_DISK_MB}MB required to start a download."
        )


def _safe_unlink(path: Path | None) -> None:
    if path is None:
        return
    try:
        path.unlink(missing_ok=True)
    except OSError as exc:
        logger.warning("could not delete %s: %s", path, exc)


# ---------------------------------------------------------------------------
# Download (yt-dlp, streamed to disk)
# ---------------------------------------------------------------------------

def download_video(url: str, progress_cb: ProgressFn | None = None) -> VideoJob:
    """
    Stream a reel to disk via yt-dlp under strict memory limits and
    return a VideoJob. Temp data is always cleaned by the caller lifecycle.
    """
    import yt_dlp  # deferred: heavy import kept off the startup path

    _ensure_download_space()

    opts = dict(config.YDL_COMMON_OPTS)
    # Prefer a single pre-muxed mp4 under the size cap so ffmpeg never has
    # to remux a huge intermediate file into RAM-backed temp storage.
    opts["format"] = "b[ext=mp4][filesize<150M]/b[filesize<150M]/b[ext=mp4]/b"

    last_reported = {"pct": -1.0}

    def _hook(event: dict) -> None:
        if event.get("status") == "finished":
            if progress_cb:
                progress_cb("download", "Download complete", 1.0)
            return
        if progress_cb and event.get("status") == "downloading":
            total = event.get("total_bytes") or event.get("total_bytes_estimate") or 0
            done = event.get("downloaded_bytes") or 0
            if total:
                pct = min(0.99, done / total)
                # throttle: only report when moved >= 5%
                if pct - last_reported["pct"] >= 0.05:
                    last_reported["pct"] = pct
                    progress_cb("download", "Downloading", pct)

    opts["progress_hooks"] = [_hook]
    before = {p for p in config.DOWNLOAD_DIR.iterdir()}

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            meta = ydl.extract_info(url, download=True)
    except Exception as exc:
        _cleanup_new_files(before)
        gc.collect()
        compact = re.sub(r"\s+", " ", str(exc))[:180]
        raise DownloadError(f"Download failed: {compact}") from exc

    path = _locate_output(meta, before)
    if not path:
        _cleanup_new_files(before)
        gc.collect()
        raise DownloadError("Download finished but no output file was found.")

    if path.stat().st_size > config.MAX_VIDEO_MB * 1024 * 1024:
        _safe_unlink(path)
        gc.collect()
        raise DownloadError(
            f"Video exceeds the {config.MAX_VIDEO_MB}MB budget "
            "for the 256MB container."
        )

    title = (meta or {}).get("title") or path.stem
    job = VideoJob(
        url=url,
        file_path=path,
        caption=title[:2000],
        ext=path.suffix.lstrip(".") or "mp4",
    )
    gc.collect()
    return job


def _locate_output(meta: dict | None, before: set) -> Path | None:
    candidates = {p for p in config.DOWNLOAD_DIR.iterdir()} - before
    if not candidates and meta and meta.get("_filename"):
        candidate = Path(meta["_filename"])
        if candidate.exists():
            return candidate
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _cleanup_new_files(before: set) -> None:
    for p in {p for p in config.DOWNLOAD_DIR.iterdir()} - before:
        if p.is_file():
            _safe_unlink(p)


# ---------------------------------------------------------------------------
# Thumbnail pipeline (Pillow, strictly transient)
# ---------------------------------------------------------------------------

def prepare_thumbnail(video_path: Path) -> Path | None:
    """Use the global custom thumb when present, else extract a frame."""
    if config.THUMB_PATH.exists():
        return config.THUMB_PATH
    return _extract_frame(video_path)


def _extract_frame(video_path: Path) -> Path | None:
    out = video_path.with_suffix(".thumb.jpg")
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", "1", "-i", str(video_path), "-frames:v", "1",
        "-vf", "scale=480:-2", str(out),
    ]
    try:
        subprocess.run(cmd, check=True, timeout=60, capture_output=True)
    except Exception as exc:
        logger.warning("frame extraction failed: %s", exc)
        _safe_unlink(out)
        return None
    if out.exists() and out.stat().st_size > 0:
        return out
    return None


def ensure_thumb_dimensions(path: Path) -> Path:
    """instagrapi requires cover images between 320px and 1440px wide."""
    from PIL import Image

    with Image.open(path) as img:
        w, h = img.size
        if 320 <= w <= 1440:
            return path
        scale = (320 / w) if w < 320 else (1440 / w)
        img = img.convert("RGB")
        img = img.resize((max(320, round(w * scale)), max(320, round(h * scale))))
        out = path.with_name(path.stem + "_fit.jpg")
        img.save(out, "JPEG", quality=80)
    return out


# ---------------------------------------------------------------------------
# Instagram via instagrapi (pure HTTP session)
# ---------------------------------------------------------------------------

def login_instagram(username: str, password: str, verification_code: str = "") -> str:
    """
    Fresh login used by the dashboard's "Add Instagram" form.
    Returns instagrapi settings JSON (stored as session_data in the DB).
    Raises TwoFactorRequiredError when a 2FA code is needed — the dashboard
    then pops the 2FA code modal.
    """
    from instagrapi import Client
    from instagrapi.exceptions import TwoFactorRequiredError

    cl = Client()
    try:
        cl.login(username, password, code=verification_code)
    except TwoFactorRequiredError as exc:
        raise RuntimeError("2FA verification code required") from exc
    return json.dumps(cl.get_settings())


def upload_to_instagram(username: str, session_data: str, job: VideoJob) -> str:
    """Post a reel with instagrapi. Returns the media code/pk on success."""
    from instagrapi import Client

    cl = Client()
    cl.delay_range = [1, 3]
    try:
        settings = json.loads(session_data)
    except ValueError as exc:
        raise RuntimeError("Instagram session data is corrupted.") from exc
    cl.set_settings(settings)

    # Verify the session is actually alive before spending time on upload.
    try:
        cl.user_info_by_username(username)
    except Exception as exc:
        raise RuntimeError(
            "Instagram session expired or invalid. Re-add the account."
        ) from exc

    thumb_arg = None
    thumb = prepare_thumbnail(job.file_path)
    if thumb:
        try:
            thumb_arg = ensure_thumb_dimensions(thumb)
        except Exception as exc:
            logger.warning("thumb prep failed: %s", exc)

    caption = job.caption or "✨ ReelPilot"
    media = None
    try:
        try:
            media = cl.clip_upload(job.file_path, caption=caption, thumbnail=thumb_arg)
        except TypeError:
            # instagrapi builds without clip thumbnail support
            media = cl.clip_upload(job.file_path, caption=caption)
    except Exception:
        # fall back to the generic video endpoint for older account types
        media = cl.video_upload(job.file_path, caption=caption, thumbnail=thumb_arg)

    code = ""
    if media is not None:
        code = getattr(media, "code", "") or str(getattr(media, "pk", ""))

    # Transient thumbnails are deleted immediately; the custom thumb persists.
    if thumb_arg and thumb_arg != config.THUMB_PATH:
        _safe_unlink(thumb_arg)
    if thumb and thumb != config.THUMB_PATH and thumb_arg != thumb:
        _safe_unlink(thumb)
    gc.collect()
    return code


# ---------------------------------------------------------------------------
# TikTok via Netscape-cookie session (pure requests, no browser)
# ---------------------------------------------------------------------------

_TT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

_TT_BASE_PARAMS = {
    "aid": "1988",
    "app_language": "en",
    "app_name": "tiktok_web",
    "browser_language": "en-US",
    "browser_name": "Mozilla",
    "browser_online": "true",
    "browser_platform": "Win32",
    "browser_version": _TT_USER_AGENT,
    "channel": "tiktok_web",
    "cookie_enabled": "true",
    "device_platform": "web_pc",
    "focus_state": "true",
    "from_page": "upload",
    "history_len": "2",
    "is_fullscreen": "false",
    "is_page_visible": "true",
    "language": "en",
    "os": "windows",
    "priority_region": "",
    "referer": "https://www.tiktok.com/upload",
    "region": "SG",
    "screen_height": "900",
    "screen_width": "1440",
    "tz_name": "Asia/Singapore",
    "webcast_language": "en",
}


def _extract_tiktok_cookies(session_data: str) -> dict:
    """Parse Netscape cookie text into a requests cookie dict."""
    cookies: dict[str, str] = {}
    for line in session_data.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 7:
            continue
        name, value = parts[5], parts[6]
        if name:
            cookies[name] = value
    return cookies


def verify_tiktok_cookies(session_data: str) -> tuple[bool, str]:
    """Validate that the pasted cookie jar holds a TikTok web session."""
    cookies = _extract_tiktok_cookies(session_data)
    if "sessionid" not in cookies:
        return False, "Cookie text must contain a 'sessionid' line."
    hint = cookies.get("unique_id") or cookies.get("sid_uid") or ""
    return True, hint


def upload_to_tiktok(session_data: str, job: VideoJob) -> str:
    """
    Upload through TikTok's web upload API with a Netscape cookie session.
    Streams the file from disk directly in the PUT body — never in RAM.
    """
    session = requests.Session()
    session.headers["User-Agent"] = _TT_USER_AGENT
    cookies = _extract_tiktok_cookies(session_data)
    if "sessionid" not in cookies:
        raise RuntimeError("TikTok cookie session is missing 'sessionid'.")
    session.cookies.update(cookies)

    params = dict(_TT_BASE_PARAMS)
    params["WebIdLastTime"] = str(int(time.time()))
    params["device_id"] = str(random.randint(73_000_000_000_000_000, 73_999_999_999_999_999))

    # 1) ask the web API for an upload slot
    slot = session.post("https://www.tiktok.com/api/upload/", params=params, timeout=30)
    slot.raise_for_status()
    try:
        payload = slot.json()
        upload_id = payload.get("data", {}).get("upload_id") or payload.get("upload_id")
    except ValueError as exc:
        raise RuntimeError("TikTok upload API returned a non-JSON response.") from exc
    if not upload_id:
        snippet = str(payload)[:120]
        raise RuntimeError(f"TikTok refused the upload session: {snippet}")
    params["upload_id"] = str(upload_id)

    # 2) stream the video bytes straight from disk
    size = job.file_path.stat().st_size
    with job.file_path.open("rb") as fh:
        put = session.put(
            "https://upload-service.tiktok.com/upload/v1/",
            params=params,
            data=fh,  # requests streams file objects — no RAM spike
            headers={"Content-Type": "video/mp4", "Content-Length": str(size)},
            timeout=600,
        )
    if not put.ok:
        raise RuntimeError(f"TikTok chunk upload failed: HTTP {put.status_code}")

    # 3) publish the post
    caption = re.sub(r"\s+", " ", job.caption or "✨ ReelPilot").strip()
    params["type"] = "post"
    post = session.post(
        "https://www.tiktok.com/api/upload/",
        params=params,
        data={"text": caption},
        timeout=30,
    )
    post.raise_for_status()
    gc.collect()
    return str(upload_id)


# ---------------------------------------------------------------------------
# Orchestrator: download once, post everywhere active
# ---------------------------------------------------------------------------

def post_everywhere(source_url: str, progress_cb: ProgressFn | None = None) -> dict:
    """
    Download the source once, then post sequentially to every active
    account with a random 3-7s delay between accounts.
    Returns {account_id: "ok:<code>"} / {account_id: "error:<msg>"}.
    """
    accounts = database.all_accounts(active_only=True)
    if not accounts:
        raise RuntimeError("No active accounts are configured yet.")

    results: dict[str, str] = {}
    job = download_video(source_url, progress_cb)
    try:
        n = len(accounts)
        for idx, acc in enumerate(accounts):
            platform = (acc["platform"] or "").lower()
            if platform not in ("instagram", "tiktok"):
                continue
            if idx > 0:
                time.sleep(random.uniform(config.ACCOUNT_DELAY_MIN, config.ACCOUNT_DELAY_MAX))
            base = 0.10 + 0.90 * (idx / n)
            span = 0.90 / n
            if progress_cb:
                progress_cb("account", acc["username"], base)
            try:
                if platform == "instagram":
                    code = upload_to_instagram(acc["username"], acc["session_data"], job)
                else:
                    code = upload_to_tiktok(acc["session_data"], job)
                database.log_upload(platform, acc["username"], source_url, "success")
                database.bump_stat("total_uploads")
                database.touch_account(acc["id"])
                results[str(acc["id"])] = f"ok:{code}"
            except Exception as exc:  # one account failing must not stop the rest
                logger.exception("upload failed for %s", acc.get("username"))
                database.log_upload(platform, acc["username"], source_url, "failed")
                results[str(acc["id"])] = f"error:{re.sub(r'[^ -~]', '?', str(exc))[:160]}"
            finally:
                if progress_cb:
                    progress_cb("account", acc["username"], min(1.0, base + span))
    finally:
        # Temp video + any stray sidecar files are gone the moment we finish.
        _safe_unlink(job.file_path)
        _cleanup_dir_strays()
        gc.collect()
    return results


def _cleanup_dir_strays() -> None:
    for p in config.DOWNLOAD_DIR.iterdir():
        if p.is_file() and not p.name.startswith("global_custom_thumb"):
            _safe_unlink(p)
