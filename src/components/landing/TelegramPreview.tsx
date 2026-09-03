import { CheckCircle2, XCircle } from "lucide-react";
import type { ReactNode } from "react";

const Bubble = ({
  side,
  children,
}: {
  side: "user" | "bot";
  children: ReactNode;
}) => (
  <div className={`flex ${side === "user" ? "justify-end" : "justify-start"}`}>
    <div
      className={
        side === "user"
          ? "max-w-[85%] rounded-2xl rounded-br-md bg-primary/15 px-4 py-2.5 text-sm text-foreground ring-1 ring-primary/25"
          : "max-w-[85%] rounded-2xl rounded-bl-md bg-secondary/70 px-4 py-2.5 text-sm text-foreground"
      }
    >
      {children}
    </div>
  </div>
);

export const TelegramPreview = () => {
  return (
    <section className="relative py-20 sm:py-24">
      <div className="section-shell grid items-center gap-12 lg:grid-cols-2">
        <div className="fade-up">
          <p className="font-mono-tech text-sm font-medium uppercase tracking-[0.2em] text-primary">
            /main.py · handlers
          </p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">
            Live progress in the chat
          </h2>
          <p className="mt-3 text-muted-foreground">
            Send a link and the bot takes over: an animated progress bar tracks
            the download, then each account posts in sequence with randomized
            pacing. Every outcome is itemized per account — code links for
            Instagram, upload IDs for TikTok.
          </p>
          <ul className="mt-6 space-y-3 text-sm">
            {[
              "Throttled edits — the bar only redraws on 5% jumps",
              "Random 3–7s delay between account posts",
              "Failed accounts reported inline, never blocking the rest",
              "Custom thumbnails via /setthumb, removed with /delthumb",
            ].map((item) => (
              <li key={item} className="flex items-start gap-2.5">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                <span className="text-muted-foreground">{item}</span>
              </li>
            ))}
          </ul>
        </div>

        <div
          className="fade-up mx-auto w-full max-w-sm rounded-[2rem] border border-border/80 bg-charcoal-deep/80 p-3 shadow-[0_24px_70px_rgba(0,0,0,0.45)]"
          style={{ animationDelay: "0.12s" }}
        >
          <div className="flex items-center gap-2.5 rounded-t-[1.6rem] border-b border-border/60 bg-secondary/40 px-4 py-3">
            <img src="/logo.svg" alt="" className="h-8 w-8 rounded-full" />
            <div>
              <p className="text-sm font-semibold">ReelPilot</p>
              <p className="text-[11px] text-primary">bot · online</p>
            </div>
          </div>

          <div className="space-y-3 p-3">
            <Bubble side="user">
              https://www.instagram.com/reel/C7xK2mNpQ4r/
            </Bubble>
            <Bubble side="bot">
              <p className="font-mono-tech text-xs text-primary">🛩 ReelPilot · Instagram</p>
              <p className="mt-1 break-all text-xs text-muted-foreground">
                🔗 C7xK2mNpQ4r
              </p>
              <p className="mt-2 font-mono-tech text-sm">[██████░░░░] 60%</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Posting → night.sessions
              </p>
            </Bubble>
            <Bubble side="bot">
              <p className="font-mono-tech text-xs text-primary">🛩 Done · Instagram</p>
              <div className="mt-2 flex flex-col gap-1.5">
                <span className="flex items-center gap-2 text-xs">
                  <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-primary" />
                  <span className="font-mono-tech">mint.reels · C7xK2mN</span>
                </span>
                <span className="flex items-center gap-2 text-xs">
                  <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-primary" />
                  <span className="font-mono-tech">night.sessions · C7xK3a</span>
                </span>
                <span className="flex items-center gap-2 text-xs">
                  <XCircle className="h-3.5 w-3.5 shrink-0 text-red-400" />
                  <span className="font-mono-tech text-muted-foreground">
                    @clips.daily · session expired
                  </span>
                </span>
              </div>
              <p className="mt-2 text-xs font-semibold">
                <span className="text-primary">2</span> posted ·{" "}
                <span className="text-red-400">1</span> failed
              </p>
            </Bubble>
          </div>
        </div>
      </div>
    </section>
  );
};
