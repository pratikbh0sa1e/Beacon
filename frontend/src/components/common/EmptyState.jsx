import React from 'react';
import { motion } from 'framer-motion';
import { FileX } from 'lucide-react';
import { Button } from '../ui/button';

export const EmptyState = ({ icon: Icon = FileX, title, description, action, actionLabel }) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="flex flex-col items-center justify-center py-12 px-4 text-center"
    >
      <div className="rounded-full bg-muted/50 p-6 mb-4">
        <Icon className="h-12 w-12 text-muted-foreground" />
      </div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground mb-6 max-w-md">{description}</p>
      {action && actionLabel && (
        <Button onClick={action}>{actionLabel}</Button>
      )}
    </motion.div>
  );
};
