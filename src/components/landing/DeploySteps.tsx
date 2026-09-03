import { Copy, Check } from "lucide-react";
import { useState } from "react";

const steps = [
  {
    title: "Create the app + volume",
    code: `fly launch --no-deploy --name reelpilot --region sin
fly volumes create bot_data --size 1 --region sin`,
  },
  {
    title: "Set the bot token",
    code: `fly secrets set TELEGRAM_BOT_TOKEN=123456:ABC-your-token \\
  WEBAPP_PUBLIC_URL=https://reelpilot.fly.dev`,
  },
  {
    title: "Ship it",
    code: `fly deploy
curl https://reelpilot.fly.dev/health
# → {"status": "healthy"}`,
  },
];

const CmdBlock = ({ code }: { code: string }) => {
  const [copied, setCopied] = useState(false);
  return (
    <div className="group relative">
      <pre className="overflow-x-auto rounded-xl border border-border/70 bg-charcoal-deep/80 px-4 py-3.5 pr-12 font-mono-tech text-xs leading-relaxed text-primary/95">
        <code>{code}</code>
      </pre>
      <button
        onClick={() => {
          navigator.clipboard?.writeText(code).catch(() => {});
          setCopied(true);
          setTimeout(() => setCopied(false), 1600);
        }}
        className="absolute right-2.5 top-2.5 rounded-lg border border-border/70 bg-card/80 p-1.5 text-muted-foreground transition-colors hover:border-primary/50 hover:text-primary"
        aria-label="Copy command"
      >
        {copied ? (
          <Check className="h-3.5 w-3.5 text-primary" />
        ) : (
          <Copy className="h-3.5 w-3.5" />
        )}
      </button>
    </div>
  );
};

export const DeploySteps = () => {
  return (
    <section id="deploy" className="relative py-20 sm:py-24">
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
            /deployment
          </p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">
            Three commands to production
          </h2>
          <p className="mt-3 text-muted-foreground">
            The machine stays running (auto-stop off, min 1 machine) so Telegram
            polling never misses an update. Persistent state lives on the
            bot_data volume at /data.
          </p>
        </div>

        <div className="grid gap-5 lg:grid-cols-3">
          {steps.map((step, i) => (
            <div
              key={step.title}
              className="fade-up rounded-2xl border border-border/80 bg-card/60 p-6"
              style={{ animationDelay: `${i * 0.1}s` }}
            >
              <div className="flex items-center gap-3">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 font-mono-tech text-sm font-bold text-primary ring-1 ring-primary/30">
                  {i + 1}
                </span>
                <h3 className="text-sm font-semibold">{step.title}</h3>
              </div>
              <div className="mt-4">
                <CmdBlock code={step.code} />
              </div>
            </div>
          ))}
        </div>

        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            ["App name", "reelpilot"],
            ["Machine", "shared-cpu-1x · 256MB"],
            ["Volume", "bot_data → /data"],
            ["Port", "8080 → 0.0.0.0"],
          ].map(([k, v]) => (
            <div
              key={k}
              className="flex items-center justify-between rounded-xl border border-border/70 bg-secondary/30 px-4 py-3"
            >
              <span className="text-xs uppercase tracking-widest text-muted-foreground">
                {k}
              </span>
              <span className="font-mono-tech text-sm font-semibold text-primary">
                {v}
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
