# ReelPilot

Cross-post reels straight from your Android phone. Send a Telegram bot any
Instagram / TikTok / Facebook / Threads link — it downloads the video once,
then publishes it to every active Instagram and TikTok account. Mint-dark web
dashboard on `:8080`, SQLite storage, zero headless browsers.

## Install (Termux, one line)

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Nadim3x/reel-pilot/main/termux-setup.sh)
```

The script installs `python`, `ffmpeg`, `clang` and friends, clones the repo
into `~/ReelPilot`, compiles the Python dependencies and grabs a wake lock.
Root is **not** required — it only helps silence Android 12+'s
phantom-process killer on rooted phones.

## Run

```bash
cd ~/ReelPilot
export TELEGRAM_BOT_TOKEN="123456:ABC…"      # from @BotFather
export IMAGEIO_FFMPEG_EXE="$(command -v ffmpeg)"
python main.py
```

Dashboard: `http://localhost:8080` (or `http://<phone-ip>:8080` from any
device on the same Wi-Fi). Default admin is `nadim` — set `ADMIN_PASSWORD`
before sharing the panel.

## Files

| File | Role |
|---|---|
| `main.py` | Telegram polling bot — approval gate, progress bars, `/setthumb` |
| `ig_handler.py` | yt-dlp streaming download → instagrapi + TikTok cookie upload |
| `dashboard.py` | Flask 3.0 panel: accounts, 2FA modal, approvals, `/health` |
| `database.py` | Self-healing SQLite (WAL, thread-safe) |
| `config.py` | Paths, yt-dlp budget options, link regexes |
| `termux-setup.sh` | The one-line installer |

Data lives in `./bot_data_local` (or `REELPILOT_DATA_DIR` if you set it).
