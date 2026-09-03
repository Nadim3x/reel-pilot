#!/data/data/com.termux/files/usr/bin/bash
# ---------------------------------------------------------------------------
# ReelPilot — one-line Termux installer.
#
#   bash <(curl -fsSL https://raw.githubusercontent.com/Nadim3x/reel-pilot/main/termux-setup.sh)
#
# Optional argument: a different repo URL (defaults to the public repo).
# Safe to run from anywhere — reuses ~/ReelPilot (or the current checkout)
# if it already exists. No root required.
# ---------------------------------------------------------------------------
set -euo pipefail

REPO_URL="${1:-https://github.com/Nadim3x/reel-pilot.git}"
APP_DIR="$HOME/ReelPilot"

mint() { printf '\033[32m\xe2\x96\xb8\033[0m %s\n' "$*"; }
die()  { printf '\033[31m\xe2\x9c\x97 %s\033[0m\n' "$*" >&2; exit 1; }

[[ -d /data/data/com.termux/files/usr ]] \
  || die "This script must run inside Termux (install it from F-Droid — the Play Store build is outdated)."

mint "Installing packages: python, ffmpeg, clang, git…"
pkg update -y >/dev/null 2>&1 || true
pkg install -y python python-pip ffmpeg git clang libjpeg-turbo binutils \
  || die "pkg install failed — run 'pkg update && pkg upgrade', then retry"

if [[ -f "$PWD/main.py" && -f "$PWD/requirements.txt" ]]; then
  APP_DIR="$PWD"                      # already inside a checkout
elif [[ -d "$APP_DIR" ]]; then
  mint "Found existing checkout at ~/ReelPilot — pulling latest…"
  git -C "$APP_DIR" pull --ff-only || true
else
  mint "Cloning ReelPilot…"
  git clone --depth 1 "$REPO_URL" "$APP_DIR" || die "git clone failed"
fi
cd "$APP_DIR" || die "cannot enter $APP_DIR"
[[ -f main.py ]] || die "main.py not found — is this the ReelPilot repo?"

mint "Installing Python dependencies (Pillow & friends compile from source — this takes a few minutes)…"
PIP_FLAGS=""
pip install --help 2>/dev/null | grep -q -- --break-system-packages && PIP_FLAGS="--break-system-packages"
# shellcheck disable=SC2086
pip install $PIP_FLAGS -r requirements.txt \
  || die "pip install failed — scroll up for the compiler error"

mint "Acquiring wake lock so Android keeps the bot alive…"
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock || true

cat <<'BANNER'

  -------------------------------------------------------------
   ReelPilot installed at: ~/ReelPilot
  -------------------------------------------------------------

  Run it:

      cd ~/ReelPilot
      export TELEGRAM_BOT_TOKEN="123456:ABC…"      # from @BotFather
      export IMAGEIO_FFMPEG_EXE="$(command -v ffmpeg)"
      python main.py

  Dashboard:  http://localhost:8080
              (default admin: nadim — set ADMIN_PASSWORD before
               opening the panel to other devices on your Wi-Fi)

  Stay-alive checklist:
      * Android Settings -> Apps -> Termux -> Battery -> Unrestricted
      * termux-wake-lock is on (re-run it after every reboot)
      * Termux:Boot add-on starts the bot automatically on reboot
      * Rooted only: disable the phantom-process killer once —
        su -c 'device_config put activity_manager max_phantom_processes 2147483647'

BANNER
