import React, { useEffect } from 'react';
import { useAuthStore } from '@/store';

interface AuthGuardProps {
  children: React.ReactNode;
}

const AuthGuard: React.FC<AuthGuardProps> = ({ children }) => {
  const { isAuthenticated, checkAuth, login } = useAuthStore();

  useEffect(() => {
    checkAuth();
    
    // Auto-login for development/testing
    if (!isAuthenticated) {
      const demoUser = {
        id: 'demo-user',
        email: 'demo@otomeshon.com',
        name: 'Demo User',
        roles: ['admin'],
        groups: ['administrators']
      };
      login(demoUser, 'demo-token');
    }
  }, [checkAuth, isAuthenticated, login]);

  // For development, always allow access
  return <>{children}</>;
};

export default AuthGuard;
