// import React from 'react';
// import { Navigate } from 'react-router-dom';
// import { useAuthStore } from '../stores/authStore';

// export const PublicRoute = ({ children }) => {
//   const { isAuthenticated, user } = useAuthStore();

//   if (isAuthenticated) {
//     if (!user?.approved) {
//       return <Navigate to="/pending-approval" replace />;
//     }
//     return <Navigate to="/" replace />;
//   }

//   return children;
// };
import React from "react";
import { Navigate } from "react-router-dom";
import { useAuthStore } from "../stores/authStore";

export const PublicRoute = ({ children }) => {
  const { isAuthenticated, user } = useAuthStore();

  // ✅ FIXED: Only redirect to pending-approval if user is NOT approved
  // Developer accounts are created with approved=true, so they won't get stuck here
  if (isAuthenticated) {
    // Check if user is approved
    if (user?.approved === false) {
      return <Navigate to="/pending-approval" replace />;
    }
    // User is authenticated and approved, go to dashboard
    return <Navigate to="/" replace />;
  }

  // Not authenticated, show public page (login/register)
  return children;
};
