// FeatureCard.jsx - Individual feature card component

import React from "react";
import { motion } from "framer-motion";
import { Card, CardContent } from "../ui/card";

export const FeatureCard = ({ icon: Icon, title, description, delay = 0 }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-100px" }}
      transition={{ duration: 0.5, delay }}
    >
      <Card className="glass-card h-full hover:neon-glow transition-all duration-300 group">
        <CardContent className="p-6">
          <div className="flex flex-col items-center text-center space-y-4">
            {/* Icon */}
            <div className="h-16 w-16 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
              <Icon className="h-8 w-8 text-primary-foreground" />
            </div>

            {/* Title */}
            <h3 className="text-xl font-semibold">{title}</h3>

            {/* Description */}
            <p className="text-muted-foreground text-sm leading-relaxed">
              {description}
            </p>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};
