import { useEffect, useState } from "react";
import { useAuthStore } from "../../stores/authStore";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { Button } from "../ui/button";
import { Clock, LogOut } from "lucide-react";

export const SessionWarningModal = () => {
  const { showSessionWarning, extendSession, logout } = useAuthStore();
  const [countdown, setCountdown] = useState(300); // 5 minutes in seconds

  useEffect(() => {
    if (showSessionWarning) {
      setCountdown(300);
      const interval = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(interval);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [showSessionWarning]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const handleStayLoggedIn = () => {
    extendSession();
  };

  const handleLogout = () => {
    logout("Logged out by user");
  };

  return (
    <Dialog open={showSessionWarning} onOpenChange={() => {}}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-yellow-500" />
            Session Expiring Soon
          </DialogTitle>
          <DialogDescription>
            Your session will expire in{" "}
            <span className="font-bold text-yellow-500">
              {formatTime(countdown)}
            </span>{" "}
            due to inactivity. Would you like to stay logged in?
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="flex-col sm:flex-row gap-2">
          <Button
            variant="outline"
            onClick={handleLogout}
            className="w-full sm:w-auto"
          >
            <LogOut className="h-4 w-4 mr-2" />
            Log Out
          </Button>
          <Button onClick={handleStayLoggedIn} className="w-full sm:w-auto">
            Stay Logged In
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
