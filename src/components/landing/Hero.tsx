import { ArrowRight, Gauge, ShieldCheck, Cpu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export const Hero = () => {
  return (
    <section className="relative overflow-hidden">
      {/* backdrop */}
      <div className="grid-bg absolute inset-0" aria-hidden="true" />
      <div
        className="absolute inset-0"
        aria-hidden="true"
        style={{
          background:
            "radial-gradient(60% 50% at 50% 0%, rgba(0,230,118,0.10) 0%, transparent 70%)",
        }}
      />
      <div className="section-shell relative flex flex-col items-center pb-16 pt-20 text-center sm:pt-28">
        <div className="fade-up flex flex-col items-center gap-6">
          <Badge
            variant="outline"
            className="gap-2 rounded-full border-primary/30 bg-primary/10 px-4 py-1.5 text-xs font-medium tracking-wide text-primary"
          >
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-60" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-primary" />
            </span>
            Fly.io shared-cpu-1x · 256MB RAM · region sin
          </Badge>

          <h1 className="max-w-4xl text-balance text-4xl font-bold leading-tight tracking-tight sm:text-6xl">
            Cross-post reels on a{" "}
            <span className="text-primary text-glow">256MB budget</span>
          </h1>

          <p className="max-w-2xl text-pretty text-base leading-relaxed text-muted-foreground sm:text-lg">
            ReelPilot is a featherweight Telegram bot + web panel that downloads a
            reel once and publishes it to every active Instagram and TikTok
            account — streamed to disk, garbage-collected on schedule, and
            strictly free of headless browsers.
          </p>

          <div className="mt-2 flex w-full flex-wrap items-center justify-center gap-3">
            <Button
              asChild
              size="lg"
              className="rounded-full bg-primary px-7 text-base font-semibold text-primary-foreground shadow-[0_0_32px_rgba(0,230,118,0.35)] hover:bg-primary/90"
            >
              <a href="#deploy">
                Launch the stack
                <ArrowRight className="ml-1 h-4 w-4" />
              </a>
            </Button>
            <Button
              asChild
              variant="outline"
              size="lg"
              className="rounded-full border-border bg-transparent px-7 text-base hover:border-primary/60 hover:text-primary"
            >
              <a href="#pipeline">See the pipeline</a>
            </Button>
          </div>

          <dl className="mt-10 grid w-full max-w-3xl grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              { icon: Gauge, value: "256MB", label: "RAM ceiling" },
              { icon: ShieldCheck, value: "0", label: "headless browsers" },
              { icon: Cpu, value: "1x", label: "shared CPU" },
              { icon: ArrowRight, value: "16K", label: "stream chunks" },
            ].map(({ icon: Icon, value, label }) => (
              <div
                key={label}
                className="flex items-center gap-3 rounded-2xl border border-border/80 bg-card/60 px-4 py-3 text-left backdrop-blur-sm"
              >
                <Icon className="h-5 w-5 shrink-0 text-primary" />
                <div>
                  <dt className="font-mono-tech text-lg font-bold leading-none text-foreground">
                    {value}
                  </dt>
                  <dd className="mt-1 text-xs text-muted-foreground">{label}</dd>
                </div>
              </div>
              ))}
          </dl>
        </div>
      </div>
    </section>
  );
};
