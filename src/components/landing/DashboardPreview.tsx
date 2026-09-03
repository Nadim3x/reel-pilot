import { Instagram, Music2, Users, Activity, CheckCircle2, PauseCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";

const StatCard = ({ label, value, sub }: { label: string; value: string; sub?: string }) => (
  <div className="rounded-2xl border border-border/80 bg-card/70 p-5">
    <p className="text-[11px] font-medium uppercase tracking-widest text-muted-foreground">
      {label}
    </p>
    <p className="font-mono-tech mt-2 text-2xl font-bold text-primary">{value}</p>
    {sub && <p className="mt-1 text-xs text-muted-foreground">{sub}</p>}
  </div>
);

export const DashboardPreview = () => {
  return (
    <section id="dashboard" className="relative py-20 sm:py-24">
      <div className="section-shell">
        <div className="mb-10 flex flex-col items-start gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="font-mono-tech text-sm font-medium uppercase tracking-[0.2em] text-primary">
              /dashboard.py
            </p>
            <h2 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">
              Mint terminal, full control
            </h2>
            <p className="mt-3 max-w-xl text-muted-foreground">
              The Flask panel binds 0.0.0.0:8080 in dark mode with a #00E676
              accent. Admins manage accounts and approvals; guests see community
              analytics only — never the account list.
            </p>
          </div>
          <Badge
            variant="outline"
            className="rounded-full border-primary/30 bg-primary/10 px-4 py-1.5 text-xs text-primary"
          >
            waitress · 4 threads
          </Badge>
        </div>

        <div className="grid gap-5 lg:grid-cols-5">
          {/* admin card */}
          <div className="fade-up rounded-3xl border border-border/80 bg-card/50 p-6 lg:col-span-3">
            <div className="mb-5 flex flex-wrap items-center gap-2">
              <Badge className="border-primary/40 bg-primary/10 text-primary">admin</Badge>
              <span className="text-xs text-muted-foreground">nadim · /admin</span>
            </div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <StatCard label="Accounts" value="4" />
              <StatCard label="Active" value="3" />
              <StatCard label="Pending" value="2" />
              <StatCard label="Reels" value="128" />
            </div>

            <div className="mt-6 overflow-hidden rounded-2xl border border-border/70">
              <div className="border-b border-border/70 bg-secondary/40 px-5 py-3 text-xs uppercase tracking-widest text-muted-foreground">
                Linked accounts
              </div>
              <ul className="divide-y divide-border/60">
                {[
                  { icon: Instagram, platform: "INSTAGRAM", user: "mint.reels", state: "live" },
                  { icon: Instagram, platform: "INSTAGRAM", user: "night.sessions", state: "live" },
                  { icon: Music2, platform: "TIKTOK", user: "@viralloop", state: "live" },
                  { icon: Music2, platform: "TIKTOK", user: "@clips.daily", state: "paused" },
                ].map(({ icon: Icon, platform, user, state }) => (
                  <li
                    key={user}
                    className="flex flex-wrap items-center justify-between gap-3 px-5 py-4"
                  >
                    <span className="flex items-center gap-3">
                      <Icon className="h-4 w-4 text-primary" />
                      <span className="font-mono-tech text-sm">{user}</span>
                    </span>
                    <span className="flex flex-wrap items-center gap-2">
                      <Badge variant="outline" className="text-muted-foreground">
                        {platform}
                      </Badge>
                      {state === "live" ? (
                        <Badge className="gap-1 border-primary/40 bg-primary/10 text-primary">
                          <CheckCircle2 className="h-3 w-3" /> live
                        </Badge>
                      ) : (
                        <Badge
                          variant="outline"
                          className="gap-1 border-amber-400/40 text-amber-300"
                        >
                          <PauseCircle className="h-3 w-3" /> paused
                        </Badge>
                      )}
                    </span>
                  </li>
                ))}
              </ul>
            </div>

            <p className="mt-4 text-xs text-muted-foreground">
              Buttons wrap with flex-wrap — Pause / Activate / Delete never clip
              on narrow screens.
            </p>
          </div>

          {/* guest card */}
          <div className="fade-up rounded-3xl border border-border/80 bg-card/50 p-6 lg:col-span-2" style={{ animationDelay: "0.12s" }}>
            <div className="mb-5 flex flex-wrap items-center gap-2">
              <Badge variant="outline" className="text-muted-foreground">
                guest · /
              </Badge>
              <span className="text-xs text-muted-foreground">open analytics view</span>
            </div>
            <div className="grid gap-3">
              <StatCard label="Reels posted" value="128" sub="all-time uploads" />
              <StatCard label="Active creators" value="3" sub="accounts with posts" />
            </div>
            <div className="mt-4 flex items-center gap-3 rounded-2xl border border-primary/25 bg-primary/5 px-4 py-3">
              <Activity className="h-5 w-5 shrink-0 text-primary" />
              <div>
                <p className="font-mono-tech text-sm font-bold text-primary">HEALTHY</p>
                <p className="text-xs text-muted-foreground">
                  uptime 41.2h · 940MB disk free
                </p>
              </div>
            </div>
            <div className="mt-4 flex items-start gap-3 rounded-2xl border border-border/70 bg-secondary/30 px-4 py-3">
              <Users className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
              <p className="text-xs leading-relaxed text-muted-foreground">
                Strict privacy: the connected social account list is hidden from
                this view. Only aggregate community numbers are public.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
