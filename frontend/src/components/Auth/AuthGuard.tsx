import React, { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/store';

interface AuthGuardProps {
  children: React.ReactNode;
}

const AuthGuard: React.FC<AuthGuardProps> = ({ children }) => {
  const { isAuthenticated, checkAuth, login } = useAuthStore();
  const location = useLocation();

  useEffect(() => {
    checkAuth();
    
    // Auto-login for development/testing
    if (!isAuthenticated) {
      const demoUser = {
        id: 'demo-user',
        email: 'demo@otomeshon.com',
        name: 'Demo User',
        role: 'admin',
        avatar: '',
        preferences: {},
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      login(demoUser, 'demo-token');
    }
  }, [checkAuth, isAuthenticated, login]);

  // For development, always allow access
  return <>{children}</>;
};

export default AuthGuard;