// FlowStep.jsx - Individual flow step component

import React from "react";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

export const FlowStep = ({ icon: Icon, title, description, index }) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.4, delay: index * 0.1 }}
      className="w-full"
    >
      <div className="glass-card p-6 hover:neon-glow transition-all duration-300 h-full border-border/50">
        <div className="flex items-start gap-4">
          {/* Step Number & Icon */}
          <div className="flex-shrink-0">
            <div className="h-12 w-12 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center neon-glow">
              <Icon className="h-6 w-6 text-primary-foreground" />
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-semibold text-primary">
                STEP {index + 1}
              </span>
            </div>
            <h4 className="font-semibold mb-1 text-base">{title}</h4>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {description}
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
