import { useLocation } from "react-router-dom";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    console.error(
      "404 Error: User attempted to access non-existent route:",
      location.pathname,
    );
  }, [location.pathname]);

  return (
    <div className="grid-bg flex min-h-screen items-center justify-center bg-background px-4">
      <div className="fade-up w-full max-w-md rounded-3xl border border-border/80 bg-card/70 p-10 text-center shadow-[0_24px_70px_rgba(0,0,0,0.45)]">
        <img src="/logo.svg" alt="ReelPilot" className="mx-auto h-16 w-16" />
        <p className="font-mono-tech mt-6 text-6xl font-bold text-primary text-glow">404</p>
        <p className="mt-3 text-muted-foreground">
          This route never made it past the memory budget.
        </p>
        <Button
          asChild
          className="mt-8 rounded-full bg-primary px-8 font-semibold text-primary-foreground hover:bg-primary/90"
        >
          <a href="/">Back to base</a>
        </Button>
      </div>
    </div>
  );
};

export default NotFound;
