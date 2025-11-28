import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

export const PublicRoute = ({ children }) => {
  const { isAuthenticated, user } = useAuthStore();

  if (isAuthenticated) {
    if (!user?.approved) {
      return <Navigate to="/pending-approval" replace />;
    }
    return <Navigate to="/" replace />;
  }

  return children;
};
