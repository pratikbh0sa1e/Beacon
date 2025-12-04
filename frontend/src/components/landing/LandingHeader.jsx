// LandingHeader.jsx - Header component for landing page

import React from "react";
import { Link } from "react-router-dom";
import { Button } from "../ui/button";
import { ThemeToggle } from "../layout/ThemeToggle";

export const LandingHeader = ({ transparent = false }) => {
  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        transparent ? "bg-transparent" : "bg-background/80 backdrop-blur-md border-b border-border/50"
      }`}
    >
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo and Branding */}
          <Link to="/" className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center neon-glow">
              <span className="text-xl font-bold text-primary-foreground">B</span>
            </div>
            <span className="text-2xl font-bold gradient-text">BEACON</span>
          </Link>

          {/* Navigation */}
          <div className="flex items-center gap-4">
            <ThemeToggle />
            <Link to="/login">
              <Button variant="ghost" className="hidden sm:inline-flex">
                Sign In
              </Button>
            </Link>
            <Link to="/register">
              <Button className="neon-glow">Get Started</Button>
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
};
