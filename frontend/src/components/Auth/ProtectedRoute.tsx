import React, { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/store';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: string;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRole
}) => {
  const { isAuthenticated, user } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const pathname = location.pathname;

  const hasRequiredRole =
    !requiredRole || user?.roles?.includes(requiredRole) || user?.roles?.includes('admin');

  useEffect(() => {
    if (!isAuthenticated) {
      navigate(`/login?from=${encodeURIComponent(pathname || '/')}`, { replace: true });
    } else if (!hasRequiredRole) {
      navigate('/unauthorized', { replace: true });
    }
  }, [isAuthenticated, hasRequiredRole, navigate, pathname]);

  if (!isAuthenticated || !hasRequiredRole) {
    return null; // Will redirect via the effect above
  }

  return <>{children}</>;
};
