// LandingPage.jsx - Main landing page component

import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { LandingHeader } from "../components/landing/LandingHeader";
import { HeroSection } from "../components/landing/HeroSection";
import { FeaturesSection } from "../components/landing/FeaturesSection";
import { SystemFlowSection } from "../components/landing/SystemFlowSection";
import { DemoVideoSection } from "../components/landing/DemoVideoSection";
import { TargetAudienceSection } from "../components/landing/TargetAudienceSection";
import { LandingFooter } from "../components/landing/LandingFooter";
import { useAuthStore } from "../stores/authStore";

export const LandingPage = () => {
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuthStore();

  useEffect(() => {
    // Redirect authenticated and approved users to dashboard
    if (isAuthenticated && user?.approved) {
      navigate("/", { replace: true });
    }
  }, [isAuthenticated, user, navigate]);

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
