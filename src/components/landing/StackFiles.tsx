import { useState } from "react";
import {
  Braces,
  Database,
  FileCode2,
  FlaskConical,
  Send,
  Settings2,
  Container,
  FileJson,
} from "lucide-react";

type FileSpec = {
  name: string;
  icon: typeof Settings2;
  desc: string;
  code: string;
};

const files: FileSpec[] = [
  {
    name: "config.py",
    icon: Settings2,
    desc: "Fallback paths /data → ./bot_data.db, yt-dlp budget options, link regexes",
    code: `def _pick_data_dir() -> Path:
    preferred = Path(os.getenv("REELPILOT_DATA_DIR", "/data"))
    try:
        preferred.mkdir(parents=True, exist_ok=True)
        probe = preferred / ".write_probe"
        probe.write_text("ok")
        probe.unlink(missing_ok=True)
        return preferred
    except OSError:
        fallback = Path.cwd() / "bot_data_local"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback

YDL_COMMON_OPTS = {
    "http_chunk_size": 16384,   # 16K stream chunks
    "ratelimit": 5 * 1024 * 1024,  # --limit-rate 5M
    "concurrent_fragment_downloads": 1,
    "socket_timeout": 30,
}`,
  },
  {
    name: "database.py",
    icon: Database,
    desc: "Self-healing schema: detects legacy tables, renames, migrates shared columns",
    code: `def _should_rebuild(conn, table) -> bool:
    if not _table_exists(conn, table):
        return True
    cols = {name.upper(): dtype for name, dtype in _columns(conn, table)}
    if "PASSWORD" in cols and "SESSION_DATA" not in cols:
        return True  # pre-2FA legacy layout
    if "IS_ACTIVE" in cols and cols["IS_ACTIVE"].startswith("TEXT"):
        return True
    return False

# WAL journal + 2MB page cache — safe with the dashboard
# reading from its thread while the bot writes.`,
  },
  {
    name: "ig_handler.py",
    icon: FileCode2,
    desc: "yt-dlp streaming download, instagrapi posting, TikTok cookie uploader",
    code: `def download_video(url, progress_cb=None) -> VideoJob:
    import yt_dlp  # deferred — off the startup path
    _ensure_download_space()
    opts = dict(config.YDL_COMMON_OPTS)
    opts["format"] = "b[ext=mp4][filesize<150M]/b[filesize<150M]/b"
    before = {p for p in config.DOWNLOAD_DIR.iterdir()}
    with yt_dlp.YoutubeDL(opts) as ydl:
        meta = ydl.extract_info(url, download=True)
    # ... then post_everywhere() fans out sequentially
    # and finally: unlink temp + gc.collect()`,
  },
  {
    name: "dashboard.py",
    icon: FlaskConical,
    desc: "Flask 3.0 panel on 0.0.0.0:8080 — admin/guest modes, approvals, /health",
    code: `@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

@app.route("/admin", methods=["POST"])
def admin_actions():
    if not is_admin():
        return jsonify({"ok": False, "error": "unauthorized"}), 403
    action = request.form.get("action", "")
    # toggle_account · delete_account · review_user
    # add_instagram (2FA-aware) · add_tiktok (cookie import)`,
  },
  {
    name: "main.py",
    icon: Send,
    desc: "Telegram polling bot — progress bars, thumbnails, approval gate",
    code: `def progress_bar(pct: float, width: int = 10) -> str:
    pct = max(0.0, min(1.0, pct))
    filled = int(round(pct * width))
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {int(pct * 100)}%"

SUPER_ADMIN_ID = 5668590673  # everyone else needs approval
# /start /help /setthumb /delthumb + link detection`,
  },
  {
    name: "Dockerfile",
    icon: Container,
    desc: "python:3.11-slim + ffmpeg only — multi-stage wheels, <300MB image",
    code: `FROM python:3.11-slim AS builder
RUN pip wheel --wheel-dir /wheels -r requirements.txt

FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 MALLOC_ARENA_MAX=2
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \\
 && rm -rf /var/lib/apt/lists/*
USER reelpilot
ENTRYPOINT ["python", "-u", "main.py"]`,
  },
  {
    name: "fly.toml",
    icon: FileJson,
    desc: "sin region, port 8080, bot_data volume, machines always on",
    code: `app = "reelpilot"
primary_region = "sin"

[http_service]
  internal_port = 8080
  auto_stop_machines = "off"
  min_machines_running = 1

[[mounts]]
  source = "bot_data"
  destination = "/data"

[[vm]]
  size = "shared-cpu-1x"
  memory_mb = 256`,
  },
];

export const StackFiles = () => {
  const [active, setActive] = useState(0);
  const current = files[active];

  return (
    <section id="stack" className="relative py-20 sm:py-24">
      <div
        className="absolute inset-x-0 top-0 h-px"
        style={{
          background:
            "linear-gradient(90deg, transparent, rgba(0,230,118,0.4), transparent)",
        }}
      />
      <div className="section-shell">
        <div className="mb-10 max-w-2xl">
          <p className="font-mono-tech text-sm font-medium uppercase tracking-[0.2em] text-primary">
            /the stack
          </p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">
            Seven files, one lean machine
          </h2>
        </div>

        <div className="grid gap-5 lg:grid-cols-5">
          <div className="flex flex-col gap-2.5 lg:col-span-2">
            {files.map((file, i) => {
              const Icon = file.icon;
              const isActive = i === active;
              return (
                <button
                  key={file.name}
                  onClick={() => setActive(i)}
                  className={`flex items-start gap-3.5 rounded-2xl border p-4 text-left transition-all ${
                    isActive
                      ? "border-primary/50 bg-primary/10"
                      : "border-border/70 bg-card/40 hover:border-border"
                  }`}
                >
                  <Icon
                    className={`mt-0.5 h-5 w-5 shrink-0 ${
                      isActive ? "text-primary" : "text-muted-foreground"
                    }`}
                  />
                  <span>
                    <span
                      className={`font-mono-tech block text-sm font-semibold ${
                        isActive ? "text-primary" : "text-foreground"
                      }`}
                    >
                      {file.name}
                    </span>
                    <span className="mt-1 block text-xs leading-relaxed text-muted-foreground">
                      {file.desc}
                    </span>
                  </span>
                </button>
              );
            })}
          </div>

          <div className="overflow-hidden rounded-2xl border border-border/80 bg-charcoal-deep/80 lg:col-span-3">
            <div className="flex items-center justify-between border-b border-border/70 px-5 py-3">
              <span className="flex items-center gap-2">
                <Braces className="h-4 w-4 text-primary" />
                <span className="font-mono-tech text-sm text-primary">
                  {current.name}
                </span>
              </span>
              <span className="font-mono-tech text-xs text-muted-foreground">
                excerpt
              </span>
            </div>
            <pre className="max-h-[420px] overflow-auto px-5 py-4 font-mono-tech text-xs leading-relaxed text-foreground/90">
              <code>{current.code}</code>
            </pre>
          </div>
        </div>
      </div>
    </section>
  );
};
