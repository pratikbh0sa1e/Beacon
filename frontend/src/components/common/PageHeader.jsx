import React from 'react';
import { motion } from 'framer-motion';

export const PageHeader = ({ title, description, action, icon: Icon }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-8"
    >
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            {Icon && (
              <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Icon className="h-5 w-5 text-primary" />
              </div>
            )}
            <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
          </div>
          {description && (
            <p className="text-base text-muted-foreground max-w-3xl mt-2">
              {description}
            </p>
          )}
        </div>
        {action && <div className="flex-shrink-0">{action}</div>}
      </div>
    </motion.div>
  );
};
