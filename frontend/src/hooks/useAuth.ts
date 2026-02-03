'use client';

/**
 * Authentication hook for managing KSeF sessions.
 */

import { useState, useEffect, useCallback } from 'react';
import { authApi } from '@/lib/api';
import type { SessionStatus } from '@/types';

interface UseAuthReturn {
  isAuthenticated: boolean;
  sessionStatus: SessionStatus | null;
  loading: boolean;
  error: string | null;
  login: (nip: string) => Promise<boolean>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

export function useAuth(): UseAuthReturn {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [sessionStatus, setSessionStatus] = useState<SessionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Check session status
  const checkSession = useCallback(async () => {
    try {
      const { data, error: apiError } = await authApi.getSessionStatus();

      if (data && data.isActive) {
        setSessionStatus(data);
        setIsAuthenticated(true);
        setError(null);
      } else {
        setSessionStatus(null);
        setIsAuthenticated(false);
        // Don't set error for 404 (no session)
        if (apiError && !apiError.includes('404') && !apiError.includes('No active session')) {
          setError(apiError);
        }
      }
    } catch (e) {
      setSessionStatus(null);
      setIsAuthenticated(false);
    }
  }, []);

  // Login with NIP
  const login = async (nip: string): Promise<boolean> => {
    setLoading(true);
    setError(null);

    const { data, error: apiError } = await authApi.initSession(nip);

    if (data) {
      setIsAuthenticated(true);
      await checkSession();
      setLoading(false);
      return true;
    } else {
      setError(apiError || 'Nie udało się zalogować');
      setIsAuthenticated(false);
      setLoading(false);
      return false;
    }
  };

  // Logout
  const logout = async (): Promise<void> => {
    setLoading(true);

    try {
      await authApi.terminateSession();
    } catch {
      // Ignore errors during logout
    }

    setIsAuthenticated(false);
    setSessionStatus(null);
    setError(null);
    setLoading(false);
  };

  // Refresh session status
  const refresh = async (): Promise<void> => {
    setLoading(true);
    await checkSession();
    setLoading(false);
  };

  // Check session on mount
  useEffect(() => {
    checkSession().finally(() => setLoading(false));
  }, [checkSession]);

  // Periodic session refresh
  useEffect(() => {
    if (!isAuthenticated) return;

    const interval = setInterval(checkSession, 60000); // Check every minute
    return () => clearInterval(interval);
  }, [isAuthenticated, checkSession]);

  return {
    isAuthenticated,
    sessionStatus,
    loading,
    error,
    login,
    logout,
    refresh,
  };
}
