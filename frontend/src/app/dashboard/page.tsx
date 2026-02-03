'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';
import { Spinner } from '@/components/ui/Spinner';
import { useAuth } from '@/hooks/useAuth';
import { useSync } from '@/hooks/useSync';
import { syncApi } from '@/lib/api';
import { formatDateTime, getRelativeTime } from '@/lib/utils';
import type { SyncStatus } from '@/types';
import { FileText, Download, Upload, RefreshCw, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated, sessionStatus, loading: authLoading, logout, refresh } = useAuth();
  const { syncing, syncIssued, syncReceived, error: syncError, clearError } = useSync();

  const [issuedStatus, setIssuedStatus] = useState<SyncStatus | null>(null);
  const [receivedStatus, setReceivedStatus] = useState<SyncStatus | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  // Fetch sync status on mount
  useEffect(() => {
    if (isAuthenticated) {
      Promise.all([
        syncApi.getStatus('subject1'),
        syncApi.getStatus('subject2'),
      ]).then(([issued, received]) => {
        if (issued.data) setIssuedStatus(issued.data);
        if (received.data) setReceivedStatus(received.data);
        setStatusLoading(false);
      });
    }
  }, [isAuthenticated]);

  const handleSyncIssued = async () => {
    await syncIssued();
    const { data } = await syncApi.getStatus('subject1');
    if (data) setIssuedStatus(data);
  };

  const handleSyncReceived = async () => {
    await syncReceived();
    const { data } = await syncApi.getStatus('subject2');
    if (data) setReceivedStatus(data);
  };

  if (authLoading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <Spinner size="lg" />
      </main>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header
        session={sessionStatus}
        onRefresh={refresh}
        onLogout={logout}
        loading={authLoading}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Zarządzaj fakturami w Krajowym Systemie e-Faktur
          </p>
        </div>

        {syncError && (
          <Alert variant="error" className="mb-6" onClose={clearError}>
            {syncError}
          </Alert>
        )}

        {/* Quick actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Issued invoices */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="w-5 h-5 text-primary-600" />
                Faktury wystawione
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {statusLoading ? (
                  <Spinner />
                ) : issuedStatus?.status === 'never_synced' ? (
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Faktury nie były jeszcze synchronizowane
                  </p>
                ) : (
                  <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                    <p>Ostatnia synchronizacja: {issuedStatus?.completedAt ? getRelativeTime(issuedStatus.completedAt) : '-'}</p>
                    <p>Pobrano: {issuedStatus?.totalFetched || 0} faktur</p>
                  </div>
                )}

                <div className="flex gap-2">
                  <Button onClick={handleSyncIssued} loading={syncing}>
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Synchronizuj
                  </Button>
                  <Link href="/invoices?type=subject1">
                    <Button variant="secondary">
                      Przeglądaj
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Received invoices */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Download className="w-5 h-5 text-green-600" />
                Faktury otrzymane
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {statusLoading ? (
                  <Spinner />
                ) : receivedStatus?.status === 'never_synced' ? (
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Faktury nie były jeszcze synchronizowane
                  </p>
                ) : (
                  <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                    <p>Ostatnia synchronizacja: {receivedStatus?.completedAt ? getRelativeTime(receivedStatus.completedAt) : '-'}</p>
                    <p>Pobrano: {receivedStatus?.totalFetched || 0} faktur</p>
                  </div>
                )}

                <div className="flex gap-2">
                  <Button onClick={handleSyncReceived} loading={syncing}>
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Synchronizuj
                  </Button>
                  <Link href="/invoices?type=subject2">
                    <Button variant="secondary">
                      Przeglądaj
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Info cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <FileText className="w-12 h-12 text-gray-400 dark:text-gray-500 mx-auto mb-3" />
                <h3 className="font-medium text-gray-900 dark:text-gray-100">Przeglądaj faktury</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Zobacz wszystkie faktury zsynchronizowane z KSeF
                </p>
                <Link href="/invoices" className="mt-4 inline-block">
                  <Button variant="ghost" size="sm">
                    Przejdź do faktur
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <RefreshCw className="w-12 h-12 text-gray-400 dark:text-gray-500 mx-auto mb-3" />
                <h3 className="font-medium text-gray-900 dark:text-gray-100">Status sesji</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {sessionStatus?.isActive ? 'Sesja aktywna' : 'Brak aktywnej sesji'}
                </p>
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
                  Ref: {sessionStatus?.referenceNumber?.slice(0, 15)}...
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="w-12 h-12 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center mx-auto mb-3">
                  <span className="text-2xl">🇵🇱</span>
                </div>
                <h3 className="font-medium text-gray-900 dark:text-gray-100">Środowisko testowe</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Połączono z ksef-test.mf.gov.pl
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
