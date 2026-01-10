"use client";

import { HeroSection } from "@/components/landing/HeroSection";
import { OutcomeSection } from "@/components/landing/OutcomeSection";
import { CapabilitySection } from "@/components/landing/CapabilitySection";
import { AgenticSection } from "@/components/landing/AgenticSection";
import { ClosedLoopSection } from "@/components/landing/ClosedLoopSection";
import { ArchitectureSection } from "@/components/landing/ArchitectureSection";
import { CTASection } from "@/components/landing/CTASection";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <HeroSection />
      <OutcomeSection />
      <CapabilitySection />
      <AgenticSection />
      <ClosedLoopSection />
      <ArchitectureSection />
      <CTASection />

      {/* Footer (Simple Component) */}
      <footer className="border-t border-white/5 bg-slate-950 py-12 text-center text-sm text-slate-600">
        <p>&copy; {new Date().getFullYear()} The Sovereign Mechanica. All rights reserved.</p>
        <p className="mt-2 text-xs">System Version: TSM99-v2.1.0-RC</p>
      </footer>
    </main>
  );
}
