import React from 'react';
import { motion } from 'framer-motion';
import { Clock, Mail, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';

export const PendingApprovalPage = () => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-background via-secondary to-background" />
      <div className="absolute inset-0" style={{ backgroundImage: 'radial-gradient(circle at 1px 1px, hsl(var(--primary) / 0.1) 1px, transparent 0)', backgroundSize: '40px 40px' }} />

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md relative z-10"
      >
        <Card className="glass-card border-border/50">
          <CardHeader className="text-center space-y-4">
            <motion.div
              animate={{
                scale: [1, 1.1, 1],
                rotate: [0, 5, -5, 0],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
              className="mx-auto h-16 w-16 rounded-full bg-warning/10 flex items-center justify-center"
            >
              <Clock className="h-8 w-8 text-warning" />
            </motion.div>
            <div>
              <CardTitle className="text-2xl">Pending Approval</CardTitle>
              <CardDescription className="mt-2">
                Your account is awaiting administrator approval
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-4">
              <div className="rounded-lg bg-muted/50 p-4 space-y-2">
                <div className="flex items-center gap-2 text-sm">
                  <Mail className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Account Email:</span>
                </div>
                <p className="font-medium">{user?.email}</p>
              </div>

              <div className="rounded-lg bg-muted/50 p-4 space-y-2">
                <p className="text-sm text-muted-foreground">Requested Role:</p>
                <p className="font-medium">{user?.role}</p>
              </div>
            </div>

            <div className="rounded-lg bg-primary/5 border border-primary/20 p-4">
              <p className="text-sm text-foreground">
                Your account registration has been received. An administrator will review your request shortly.
                You will receive an email notification once your account is approved.
              </p>
            </div>

            <Button
              variant="outline"
              className="w-full"
              onClick={handleLogout}
            >
              <LogOut className="h-4 w-4 mr-2" />
              Sign Out
            </Button>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};
