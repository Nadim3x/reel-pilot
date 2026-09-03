import { Link2, Download, Upload, Trash2, MessageSquare } from "lucide-react";

const steps = [
  {
    icon: Link2,
    step: "01",
    title: "Detect the link",
    body: "Instagram, TikTok, Facebook and Threads URLs are matched by regex — no URL shortener calls, no lookups.",
  },
  {
    icon: Download,
    step: "02",
    title: "Stream to disk",
    body: "yt-dlp downloads once with 16K chunks and a 5MB/s cap. No format remux unless absolutely required.",
  },
  {
    icon: MessageSquare,
    step: "03",
    title: "Progress bar",
    body: "The Telegram message updates as [████░░░░░░] 40% — throttled to 5% jumps so edits stay cheap.",
  },
  {
    icon: Upload,
    step: "04",
    title: "Post everywhere",
    body: "Sequential posting across all active accounts via instagrapi HTTP sessions and TikTok cookie sessions, 3–7s apart.",
  },
  {
    icon: Trash2,
    step: "05",
    title: "Cleanup + gc",
    body: "Temp video unlinked immediately, thumbnails pruned, explicit gc.collect() returns arenas to the OS.",
  },
];

export const Pipeline = () => {
  return (
    <section id="pipeline" className="relative py-20 sm:py-24">
      <div className="section-shell">
        <div className="mb-12 max-w-2xl">
          <p className="font-mono-tech text-sm font-medium uppercase tracking-[0.2em] text-primary">
            /ig_handler.py
          </p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">
            One link in, every account served
          </h2>
          <p className="mt-3 text-muted-foreground">
            The media pipeline is a strict, single-threaded lifecycle. Each
            stage is memory-bounded, and a failure in one account never stops
            the rest of the fan-out.
          </p>
        </div>

        <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {steps.map(({ icon: Icon, step, title, body }, i) => (
            <li
              key={step}
              className="fade-up relative rounded-2xl border border-border/80 bg-card/60 p-5"
              style={{ animationDelay: `${i * 0.08}s` }}
            >
              <div className="flex items-center justify-between">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 ring-1 ring-primary/25">
                  <Icon className="h-5 w-5 text-primary" />
                </span>
                <span className="font-mono-tech text-xs font-bold text-primary/50">
                  {step}
                </span>
              </div>
              <h3 className="mt-4 text-sm font-semibold">{title}</h3>
              <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">
                {body}
              </p>
            </li>
          ))}
        </ol>

        <div className="mt-10 grid gap-4 lg:grid-cols-3">
          <div className="rounded-2xl border border-border/80 bg-card/60 p-6 lg:col-span-2">
            <p className="font-mono-tech text-xs uppercase tracking-widest text-muted-foreground">
              supported sources
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              {[
                "instagram.com/reel/*",
                "tiktok.com/@user/video/*",
                "facebook.com/watch/*",
                "facebook.com/reel/*",
                "threads.net/*",
                "vm.tiktok.com/*",
              ].map((src) => (
                <code
                  key={src}
                  className="rounded-full border border-border/80 bg-secondary/60 px-3.5 py-1.5 font-mono-tech text-xs text-primary/90"
                >
                  {src}
                </code>
              ))}
            </div>
          </div>
          <div className="rounded-2xl border border-primary/30 bg-primary/5 p-6">
            <p className="font-mono-tech text-xs uppercase tracking-widest text-primary/80">
              safety caps
            </p>
            <ul className="mt-4 space-y-2.5 text-sm text-muted-foreground">
              <li>
                <span className="font-mono-tech font-bold text-primary">90MB</span>{" "}
                max video size guard
              </li>
              <li>
                <span className="font-mono-tech font-bold text-primary">120MB</span>{" "}
                min free disk before download
              </li>
              <li>
                <span className="font-mono-tech font-bold text-primary">1</span>{" "}
                concurrent fragment download
              </li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
};
