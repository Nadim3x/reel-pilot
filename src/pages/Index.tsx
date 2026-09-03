import { Navbar, Footer } from "@/components/landing/Navbar";
import { Hero } from "@/components/landing/Hero";
import { Pipeline } from "@/components/landing/Pipeline";
import { DashboardPreview } from "@/components/landing/DashboardPreview";
import { MemoryBudget } from "@/components/landing/MemoryBudget";
import { FeatureGrid } from "@/components/landing/FeatureGrid";
import { TelegramPreview } from "@/components/landing/TelegramPreview";
import { StackFiles } from "@/components/landing/StackFiles";
import { InstallSteps } from "@/components/landing/InstallSteps";
import { DeployCTA } from "@/components/landing/EmptyState";
import { MadeWithDyad } from "@/components/made-with-dyad";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main>
        <Hero />
        <Pipeline />
        <DashboardPreview />
        <MemoryBudget />
        <FeatureGrid />
        <TelegramPreview />
        <StackFiles />
        <InstallSteps />
        <DeployCTA />
      </main>
      <Footer />
      <MadeWithDyad />
    </div>
  );
};

export default Index;
