// AudienceCard.jsx - Individual audience card component

import React from "react";
import { motion } from "framer-motion";
import { Card, CardContent } from "../ui/card";

export const AudienceCard = ({ icon: Icon, title, description, delay = 0 }) => {
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
            <div className="h-14 w-14 rounded-lg bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
              <Icon className="h-7 w-7 text-primary" />
            </div>

            {/* Title */}
            <h3 className="text-lg font-semibold">{title}</h3>

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
