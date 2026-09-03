import { Ban, Database, HardDriveDownload, Recycle, Timer } from "lucide-react";

const guards = [
  {
    icon: Ban,
    title: "No headless browsers",
    body: "selenium, playwright, puppeteer, chromium and chromedriver are banned — a meta-path import guard refuses them at runtime, and the Dockerfile never pulls GUI libraries.",
  },
  {
    icon: HardDriveDownload,
    title: "Streamed, never buffered",
    body: "yt-dlp writes chunks straight to disk with --buffer-size 16K and --limit-rate 5M, capping peak RSS regardless of source resolution.",
  },
  {
    icon: Recycle,
    title: "gc.collect() lifecycle",
    body: "An explicit collection runs after every download and after every upload lifecycle, returning interpreter arenas to the OS before the next job.",
  },
  {
    icon: Database,
    title: "SQLite, not a server",
    body: "WAL-journaled SQLite with a 2MB page cache keeps storage at zero extra processes. Sessions, users and counters live in one file on /data.",
  },
  {
    icon: Timer,
    title: "Sequential pacing",
    body: "Uploads post one account at a time with a random 3–7s delay — no parallel fan-out, no connection storms, no memory spikes.",
  },
  {
    icon: Ban,
    title: "Temp files vanish",
    body: "Video files are unlinked the moment an upload lifecycle ends, and a startup sweep clears any strays before the first job runs.",
  },
];

export const MemoryBudget = () => {
  return (
    <section id="memory" className="relative py-20 sm:py-24">
      <div
        className="absolute inset-x-0 top-0 h-px"
        style={{
          background:
            "linear-gradient(90deg, transparent, rgba(0,230,118,0.4), transparent)",
        }}
      />
      <div className="section-shell">
        <div className="mb-12 max-w-2xl">
          <p className="font-mono-tech text-sm font-medium uppercase tracking-[0.2em] text-primary">
            /memory budget
          </p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">
            Engineered below the OOM line
          </h2>
          <p className="mt-3 text-muted-foreground">
            Every default in ReelPilot exists to keep one shared-cpu-1x machine
            breathing. PYTHONUNBUFFERED=1 and MALLOC_ARENA_MAX=2 ship in the
            environment; the rest is discipline in code.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {guards.map(({ icon: Icon, title, body }, i) => (
            <article
              key={title}
              className="fade-up group rounded-2xl border border-border/80 bg-card/60 p-6 transition-colors hover:border-primary/40"
              style={{ animationDelay: `${i * 0.07}s` }}
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 ring-1 ring-primary/25">
                <Icon className="h-5 w-5 text-primary" />
              </div>
              <h3 className="mt-4 text-base font-semibold">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                {body}
              </p>
            </article>
          ))}
        </div>

        <div className="mt-8 overflow-hidden rounded-2xl border border-border/70 bg-charcoal-deep/70">
          <div className="flex items-center gap-2 border-b border-border/70 px-5 py-3">
            <span className="h-2.5 w-2.5 rounded-full bg-red-400/70" />
            <span className="h-2.5 w-2.5 rounded-full bg-amber-300/70" />
            <span className="h-2.5 w-2.5 rounded-full bg-primary/70" />
            <span className="ml-2 font-mono-tech text-xs text-muted-foreground">
              env · fly.toml
            </span>
          </div>
          <pre className="overflow-x-auto px-5 py-4 font-mono-tech text-xs leading-relaxed text-primary/90 sm:text-sm">
            <code>{`PORT=8080
PYTHONUNBUFFERED=1
MALLOC_ARENA_MAX=2   # two glibc arenas → no fragmentation bloat
PYTHONDONTWRITEBYTECODE=1`}</code>
          </pre>
        </div>
      </div>
    </section>
  );
};
