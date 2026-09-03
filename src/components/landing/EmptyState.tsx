import { Rocket } from "lucide-react";
import { Button } from "@/components/ui/button";

export const DeployCTA = () => {
  return (
    <section className="relative overflow-hidden py-20 sm:py-28">
      <div className="grid-bg absolute inset-0 opacity-60" aria-hidden="true" />
      <div
        className="absolute inset-0"
        aria-hidden="true"
        style={{
          background:
            "radial-gradient(50% 60% at 50% 100%, rgba(0,230,118,0.12) 0%, transparent 70%)",
        }}
      />
      <div className="section-shell relative flex flex-col items-center gap-8 text-center">
        {/* robot-pilot empty state illustration */}
        <svg
          viewBox="0 0 320 180"
          className="h-44 w-full max-w-md"
          role="img"
          aria-label="Robot pilot awaiting its first account"
        >
          {/* reel outline */}
          <circle cx="238" cy="90" r="44" fill="none" stroke="#1E2B26" strokeWidth="2" />
          <circle cx="238" cy="90" r="30" fill="none" stroke="#1E2B26" strokeWidth="1.5" />
          <circle cx="238" cy="90" r="9" fill="none" stroke="#1E2B26" strokeWidth="1.5" />
          <path d="M234 84 L 246 90 L 234 96 Z" fill="#00E676" opacity="0.9" />
          {/* dotted trajectory arc */}
          <path
            d="M78 128 C 118 64, 168 58, 196 74"
            fill="none"
            stroke="#00E676"
            strokeWidth="2"
            strokeDasharray="2 8"
            strokeLinecap="round"
            opacity="0.7"
          />
          {/* robot pilot */}
          <g stroke="#00E676" strokeWidth="2.5" fill="none" strokeLinecap="round">
            <rect x="52" y="70" width="34" height="26" rx="8" fill="#0F1714" />
            <path d="M69 96 L 69 116" />
            <path d="M56 116 L 46 126 M 82 116 L 92 126" />
            <circle cx="61" cy="83" r="2.5" fill="#00E676" stroke="none" />
            <circle cx="77" cy="83" r="2.5" fill="#00E676" stroke="none" />
            <path d="M62 90 Q 69 95 76 90" />
            <path d="M52 76 L 44 68 M 86 76 L 94 68" />
            <path d="M86 82 L 108 88" />
            <circle cx="112" cy="90" r="3" fill="#0F1714" />
          </g>
          {/* scan lines */}
          <line x1="20" y1="150" x2="300" y2="150" stroke="#1E2B26" strokeWidth="1.5" />
          <line x1="40" y1="158" x2="200" y2="158" stroke="#14201B" strokeWidth="1.5" />
        </svg>

        <h2 className="text-balance text-3xl font-bold tracking-tight sm:text-4xl">
          Ready when your first account is
        </h2>
        <p className="max-w-xl text-pretty text-muted-foreground">
          Sign in to the panel as <span className="font-mono-tech text-primary">nadim</span>,
          add an Instagram session or paste TikTok cookies, and the bot starts
          fan-out posting the moment a link lands in the chat.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Button
            asChild
            size="lg"
            className="rounded-full bg-primary px-8 text-base font-semibold text-primary-foreground shadow-[0_0_32px_rgba(0,230,118,0.35)] hover:bg-primary/90"
          >
            <a href="#deploy">
              <Rocket className="mr-1.5 h-4 w-4" />
              Deploy ReelPilot
            </a>
          </Button>
          <Button
            asChild
            variant="outline"
            size="lg"
            className="rounded-full border-border px-8 text-base hover:border-primary/60 hover:text-primary"
          >
            <a href="#dashboard">Tour the panel</a>
          </Button>
        </div>
        <p className="font-mono-tech text-xs text-muted-foreground">
          python-telegram-bot==20.7 · Flask==3.0.0 · instagrapi==2.1.2 · yt-dlp
        </p>
      </div>
    </section>
  );
};
