// LandingPage.jsx - Main landing page component

import React from "react";
import { LandingHeader } from "../components/landing/LandingHeader";
import { HeroSection } from "../components/landing/HeroSection";
import { FeaturesSection } from "../components/landing/FeaturesSection";
import { SystemFlowSection } from "../components/landing/SystemFlowSection";
import { DemoVideoSection } from "../components/landing/DemoVideoSection";
import { TargetAudienceSection } from "../components/landing/TargetAudienceSection";
import { LandingFooter } from "../components/landing/LandingFooter";

export const LandingPage = () => {
  return (
    <div className="min-h-screen">
      <LandingHeader />
      <main>
        <HeroSection />
        <FeaturesSection />
        <SystemFlowSection />
        <DemoVideoSection />
        <TargetAudienceSection />
      </main>
      <LandingFooter />
    </div>
  );
};
