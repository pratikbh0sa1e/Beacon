// FlowStep.jsx - Individual flow step component

import React from "react";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

export const FlowStep = ({ icon: Icon, title, description, index, isLast }) => {
  return (
    <div className="flex flex-col md:flex-row items-center gap-4">
      {/* Step Card */}
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        whileInView={{ opacity: 1, scale: 1 }}
        viewport={{ once: true, margin: "-50px" }}
        transition={{ duration: 0.5, delay: index * 0.1 }}
        className="flex-1"
      >
        <div className="glass-card p-6 hover:neon-glow transition-all duration-300">
          <div className="flex items-start gap-4">
            {/* Step Number & Icon */}
            <div className="flex-shrink-0">
              <div className="h-12 w-12 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center">
                <Icon className="h-6 w-6 text-primary-foreground" />
              </div>
            </div>

            {/* Content */}
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs font-semibold text-primary">
                  STEP {index + 1}
                </span>
              </div>
              <h4 className="font-semibold mb-1">{title}</h4>
              <p className="text-sm text-muted-foreground">{description}</p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Arrow Connector (hidden on mobile, shown on desktop, hidden for last item) */}
      {!isLast && (
        <div className="hidden md:block flex-shrink-0">
          <ArrowRight className="h-6 w-6 text-primary/50" />
        </div>
      )}
    </div>
  );
};
