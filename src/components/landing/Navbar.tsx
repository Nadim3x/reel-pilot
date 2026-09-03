import { Github, Terminal } from "lucide-react";

export const Navbar = () => {
  return (
    <header className="sticky top-0 z-50 border-b border-border/60 bg-background/80 backdrop-blur-md">
      <div className="section-shell flex h-16 flex-wrap items-center justify-between gap-3">
        <a href="#" className="flex items-center gap-2.5">
          <img src="/logo.svg" alt="ReelPilot logo" className="h-9 w-9" />
          <span className="text-lg font-bold tracking-tight">
            Reel<span className="text-primary">Pilot</span>
          </span>
        </a>
        <nav className="hidden items-center gap-1 text-sm text-muted-foreground md:flex">
          {[
            ["Pipeline", "#pipeline"],
            ["Dashboard", "#dashboard"],
            ["Memory", "#memory"],
            ["Stack", "#stack"],
            ["Deploy", "#deploy"],
          ].map(([label, href]) => (
            <a
              key={href}
              href={href}
              className="rounded-full px-3.5 py-2 transition-colors hover:bg-secondary hover:text-foreground"
            >
              {label}
            </a>
          ))}
        </nav>
        <a
          href="#deploy"
          className="flex items-center gap-2 rounded-full border border-primary/40 bg-primary/10 px-4 py-2 text-sm font-medium text-primary transition-colors hover:bg-primary/20"
        >
          <Terminal className="h-4 w-4" />
          fly deploy
        </a>
      </div>
    </header>
  );
};

export const Footer = () => {
  return (
    <footer className="border-t border-border/60 bg-charcoal-deep/60">
      <div className="section-shell flex flex-col items-center gap-6 py-12">
        <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-sm text-muted-foreground">
          <span className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-primary" />
            GET /health → {"{ status: healthy }"}
          </span>
          <span className="font-mono-tech">region sin · 0.0.0.0:8080</span>
          <span className="font-mono-tech">MALLOC_ARENA_MAX=2</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground/80">
          <Github className="h-3.5 w-3.5" />
          ReelPilot · engineered to stay under the OOM line
        </div>
      </div>
    </footer>
  );
};
