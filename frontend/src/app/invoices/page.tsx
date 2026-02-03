'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Alert } from '@/components/ui/Alert';
import { Spinner } from '@/components/ui/Spinner';
import { InvoiceFilters } from '@/components/invoices/InvoiceFilters';
import { InvoiceList } from '@/components/invoices/InvoiceList';
import { useAuth } from '@/hooks/useAuth';
import { useInvoices } from '@/hooks/useInvoices';
import { useSync } from '@/hooks/useSync';
import type { InvoiceQueryParams } from '@/types';

function InvoicesContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, sessionStatus, loading: authLoading, logout, refresh } = useAuth();
  const {
    invoices,
    loading: invoicesLoading,
    error: invoicesError,
    totalCount,
    pageSize,
    pageOffset,
    fetchInvoices,
    downloadInvoice,
    nextPage,
    prevPage,
    clearError: clearInvoicesError,
  } = useInvoices();
  const { syncing, syncIssued, syncReceived, error: syncError, clearError: clearSyncError } = useSync();

  const [currentSubjectType, setCurrentSubjectType] = useState<'subject1' | 'subject2'>(
    (searchParams.get('type') as 'subject1' | 'subject2') || 'subject1'
  );

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  // Fetch invoices on mount and when subject type changes
  useEffect(() => {
    if (isAuthenticated) {
      fetchInvoices({ subjectType: currentSubjectType });
    }
  }, [isAuthenticated, currentSubjectType, fetchInvoices]);

  const handleFilter = (params: InvoiceQueryParams) => {
    if (params.subjectType) {
      setCurrentSubjectType(params.subjectType);
    }
    fetchInvoices(params);
  };

  const handleSync = async () => {
    if (currentSubjectType === 'subject1') {
      await syncIssued();
    } else {
      await syncReceived();
    }
    // Refresh list after sync
    fetchInvoices({ subjectType: currentSubjectType });
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

  const error = invoicesError || syncError;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header
        session={sessionStatus}
        onRefresh={refresh}
        onLogout={logout}
        loading={authLoading}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Faktury</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            {currentSubjectType === 'subject1' ? 'Faktury wystawione' : 'Faktury otrzymane'}
          </p>
        </div>

        {error && (
          <Alert
            variant="error"
            className="mb-6"
            onClose={() => {
              clearInvoicesError();
              clearSyncError();
            }}
          >
            {error}
          </Alert>
        )}

        <Card>
          <CardHeader>
            <InvoiceFilters
              onFilter={handleFilter}
              onSync={handleSync}
              syncing={syncing}
              loading={invoicesLoading}
            />
          </CardHeader>
          <CardContent className="p-0">
            <InvoiceList
              invoices={invoices}
              loading={invoicesLoading}
              totalCount={totalCount}
              pageSize={pageSize}
              pageOffset={pageOffset}
              subjectType={currentSubjectType}
              onDownload={downloadInvoice}
              onNextPage={nextPage}
              onPrevPage={prevPage}
            />
          </CardContent>
        </Card>
      </main>
    </div>
  );
}

export default function InvoicesPage() {
  return (
    <Suspense fallback={
      <main className="min-h-screen flex items-center justify-center">
        <Spinner size="lg" />
      </main>
    }>
      <InvoicesContent />
    </Suspense>
  );
}
