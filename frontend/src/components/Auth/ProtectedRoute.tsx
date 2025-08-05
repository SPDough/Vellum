import React, { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { Box, CircularProgress } from '@mui/material';
import { useAuth } from '../../contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: string;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredRole 
}) => {
  const { isAuthenticated, user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      // Redirect to login page with return url
      router.push(`/login?from=${encodeURIComponent(pathname)}`);
    } else if (!loading && requiredRole && user?.role !== requiredRole && user?.role !== 'admin') {
      // User doesn't have required role
      router.push('/unauthorized');
    }
  }, [isAuthenticated, loading, requiredRole, user?.role, router, pathname]);

  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  if (!isAuthenticated) {
    return null; // Will redirect via useEffect
  }

  if (requiredRole && user?.role !== requiredRole && user?.role !== 'admin') {
    return null; // Will redirect via useEffect
  }

  return <>{children}</>;
};