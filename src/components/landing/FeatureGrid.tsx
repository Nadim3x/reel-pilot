import {
  Cookie,
  Fingerprint,
  Send,
  ShieldAlert,
  SlidersHorizontal,
  ImagePlus,
} from "lucide-react";

const features = [
  {
    icon: Send,
    title: "Telegram-first control",
    body: "python-telegram-bot 20.7 polling mode — /start links straight to the web dashboard, /help documents every command.",
  },
  {
    icon: ShieldAlert,
    title: "Approval gatekeeping",
    body: "Only the super admin (5668590673) and dashboard-approved users can trigger postings. Everyone else lands in a pending queue.",
  },
  {
    icon: Cookie,
    title: "Cookie-session TikTok",
    body: "Netscape cookies.txt paste-in replaces any browser uploader — validated for a sessionid line before it's ever stored.",
  },
  {
    icon: Fingerprint,
    title: "2FA-aware Instagram",
    body: "instagrapi logins surface a 6-digit code modal in the dashboard when TwoFactorRequiredError fires. No challenge loops.",
  },
  {
    icon: ImagePlus,
    title: "Custom thumbnails",
    body: "/setthumb saves any photo as /data/global_custom_thumb.jpg; every upload uses it, auto-resized into instagrapi's 320–1440px band.",
  },
  {
    icon: SlidersHorizontal,
    title: "Pause any account",
    body: "Toggle accounts live or paused from the panel. Paused accounts are skipped by the fan-out without deleting their session.",
  },
];

export const FeatureGrid = () => {
  return (
    <section className="relative py-20 sm:py-24">
      <div
        className="absolute inset-x-0 top-0 h-px"
        style={{
          background:
            "linear-gradient(90deg, transparent, rgba(0,230,118,0.4), transparent)",
        }}
      />
      <div className="section-shell">
        <div className="mb-12 flex flex-col items-start gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div className="max-w-2xl">
            <p className="font-mono-tech text-sm font-medium uppercase tracking-[0.2em] text-primary">
              /main.py
            </p>
            <h2 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">
              Everything the bot does
            </h2>
          </div>
          <span className="font-mono-tech text-xs text-muted-foreground">
            polling mode · drop_pending_updates
          </span>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.map(({ icon: Icon, title, body }, i) => (
            <article
              key={title}
              className="fade-up rounded-2xl border border-border/80 bg-card/60 p-6 transition-colors hover:border-primary/40"
              style={{ animationDelay: `${i * 0.06}s` }}
            >
              <Icon className="h-6 w-6 text-primary" />
              <h3 className="mt-4 text-base font-semibold">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                {body}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
};
