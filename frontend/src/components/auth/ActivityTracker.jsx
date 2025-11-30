import { useEffect } from "react";
import { useAuthStore } from "../../stores/authStore";

export const ActivityTracker = () => {
  const { isAuthenticated, updateActivity } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) return;

    const events = [
      "mousedown",
      "keydown",
      "scroll",
      "touchstart",
      "click",
      "mousemove",
    ];

    let activityTimeout;

    const handleActivity = () => {
      // Debounce activity updates to avoid too many calls
      clearTimeout(activityTimeout);
      activityTimeout = setTimeout(() => {
        updateActivity();
      }, 1000); // Update activity at most once per second
    };

    // Add event listeners
    events.forEach((event) => {
      window.addEventListener(event, handleActivity, { passive: true });
    });

    // Cleanup
    return () => {
      clearTimeout(activityTimeout);
      events.forEach((event) => {
        window.removeEventListener(event, handleActivity);
      });
    };
  }, [isAuthenticated, updateActivity]);

  return null; // This component doesn't render anything
};
