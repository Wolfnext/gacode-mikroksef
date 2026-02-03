'use client';

/**
 * Sync hook for managing invoice synchronization.
 */

import { useState, useCallback } from 'react';
import { syncApi } from '@/lib/api';
import type { SyncResponse, SyncStatus } from '@/types';

interface UseSyncReturn {
  syncing: boolean;
  lastSyncResult: SyncResponse | null;
  syncStatus: SyncStatus | null;
  error: string | null;
  syncIssued: (dateFrom?: string, dateTo?: string, fullSync?: boolean) => Promise<SyncResponse | null>;
  syncReceived: (dateFrom?: string, dateTo?: string, fullSync?: boolean) => Promise<SyncResponse | null>;
  getSyncStatus: (type?: 'subject1' | 'subject2') => Promise<void>;
  clearCache: () => Promise<number>;
  clearError: () => void;
}

export function useSync(): UseSyncReturn {
  const [syncing, setSyncing] = useState(false);
  const [lastSyncResult, setLastSyncResult] = useState<SyncResponse | null>(null);
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Sync issued invoices
  const syncIssued = useCallback(
    async (
      dateFrom?: string,
      dateTo?: string,
      fullSync?: boolean
    ): Promise<SyncResponse | null> => {
      setSyncing(true);
      setError(null);

      const { data, error: apiError } = await syncApi.syncIssued(dateFrom, dateTo, fullSync);

      setSyncing(false);

      if (data) {
        setLastSyncResult(data);
        return data;
      } else {
        setError(apiError || 'Synchronizacja nie powiodła się');
        return null;
      }
    },
    []
  );

  // Sync received invoices
  const syncReceived = useCallback(
    async (
      dateFrom?: string,
      dateTo?: string,
      fullSync?: boolean
    ): Promise<SyncResponse | null> => {
      setSyncing(true);
      setError(null);

      const { data, error: apiError } = await syncApi.syncReceived(dateFrom, dateTo, fullSync);

      setSyncing(false);

      if (data) {
        setLastSyncResult(data);
        return data;
      } else {
        setError(apiError || 'Synchronizacja nie powiodła się');
        return null;
      }
    },
    []
  );

  // Get sync status
  const getSyncStatus = useCallback(
    async (type: 'subject1' | 'subject2' = 'subject1'): Promise<void> => {
      const { data, error: apiError } = await syncApi.getStatus(type);

      if (data) {
        setSyncStatus(data);
      } else {
        setError(apiError || 'Nie udało się pobrać statusu synchronizacji');
      }
    },
    []
  );

  // Clear cache
  const clearCache = useCallback(async (): Promise<number> => {
    setSyncing(true);
    setError(null);

    const { data, error: apiError } = await syncApi.clearCache();

    setSyncing(false);

    if (data) {
      return data.deletedCount;
    } else {
      setError(apiError || 'Nie udało się wyczyścić cache');
      return 0;
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return {
    syncing,
    lastSyncResult,
    syncStatus,
    error,
    syncIssued,
    syncReceived,
    getSyncStatus,
    clearCache,
    clearError,
  };
}
