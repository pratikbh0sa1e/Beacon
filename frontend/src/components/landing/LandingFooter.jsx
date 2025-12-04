// LandingFooter.jsx - Footer component for landing page

import React from "react";
import { Link } from "react-router-dom";
import { Badge } from "../ui/badge";

export const LandingFooter = () => {
  return (
    <footer className="border-t border-border/50 py-12 px-4">
      <div className="container mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          {/* Branding */}
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center neon-glow">
                <span className="text-xl font-bold text-primary-foreground">B</span>
              </div>
              <span className="text-2xl font-bold gradient-text">BEACON</span>
            </div>
            <p className="text-sm text-muted-foreground mb-2">
              Government Policy Intelligence Platform
            </p>
            <div className="flex items-center gap-2">
              <Badge variant="outline">v2.0.0</Badge>
              <Badge className="bg-success text-success-foreground">
                Production Ready
              </Badge>
            </div>
          </div>

          {/* Links */}
          <div>
            <h3 className="font-semibold mb-4">Resources</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>
                <a
                  href="http://localhost:8000/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-primary transition-colors"
                >
                  API Documentation
                </a>
              </li>
              <li>
                <Link to="/login" className="hover:text-primary transition-colors">
                  Sign In
                </Link>
              </li>
              <li>
                <Link to="/register" className="hover:text-primary transition-colors">
                  Get Started
                </Link>
              </li>
            </ul>
          </div>

          {/* Info */}
          <div>
            <h3 className="font-semibold mb-4">About</h3>
            <p className="text-sm text-muted-foreground">
              Built with ❤️ for Government Policy Intelligence
            </p>
          </div>
        </div>

        {/* Copyright */}
        <div className="border-t border-border/50 pt-8 text-center text-sm text-muted-foreground">
          <p>&copy; 2025 BEACON. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};
