'use client';

import { Suspense, useCallback, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';
import { Spinner } from '@/components/ui/Spinner';
import { InvoiceFilters } from '@/components/invoices/InvoiceFilters';
import { InvoiceList } from '@/components/invoices/InvoiceList';
import { useAuth } from '@/hooks/useAuth';
import { useInvoices } from '@/hooks/useInvoices';
import { useSync } from '@/hooks/useSync';
import { invoicesApi } from '@/lib/api';
import { Search, X } from 'lucide-react';
import type { InvoiceQueryParams, InvoiceHeader } from '@/types';

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

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchMode, setIsSearchMode] = useState(false);
  const [searchResults, setSearchResults] = useState<InvoiceHeader[]>([]);
  const [searchTotal, setSearchTotal] = useState(0);
  const [searchLoading, setSearchLoading] = useState(false);

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  // Fetch invoices on mount and when subject type changes
  useEffect(() => {
    if (isAuthenticated && !isSearchMode) {
      fetchInvoices({ subjectType: currentSubjectType });
    }
  }, [isAuthenticated, currentSubjectType, fetchInvoices, isSearchMode]);

  const handleFilter = (params: InvoiceQueryParams) => {
    setIsSearchMode(false);
    setSearchQuery('');
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
    fetchInvoices({ subjectType: currentSubjectType });
  };

  const handleSearch = useCallback(async () => {
    if (searchQuery.trim().length < 2) return;

    setSearchLoading(true);
    setIsSearchMode(true);

    const { data, error } = await invoicesApi.search({
      q: searchQuery.trim(),
      subjectType: currentSubjectType,
    });

    if (data) {
      setSearchResults(data.invoiceHeaderList);
      setSearchTotal(data.numberOfElements);
    }
    setSearchLoading(false);
  }, [searchQuery, currentSubjectType]);

  const handleClearSearch = () => {
    setSearchQuery('');
    setIsSearchMode(false);
    setSearchResults([]);
    setSearchTotal(0);
    fetchInvoices({ subjectType: currentSubjectType });
  };

  const handleSearchKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
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
  const displayInvoices = isSearchMode ? searchResults : invoices;
  const displayTotal = isSearchMode ? searchTotal : totalCount;
  const displayLoading = isSearchMode ? searchLoading : invoicesLoading;

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
            {isSearchMode
              ? `Wyniki wyszukiwania: "${searchQuery}" (${searchTotal})`
              : currentSubjectType === 'subject1' ? 'Faktury wystawione' : 'Faktury otrzymane'
            }
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

        {/* Search bar */}
        <div className="mb-4 flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleSearchKeyDown}
              placeholder="Szukaj po nazwie kontrahenta, numerze faktury, opisie..."
              className="pl-10 pr-10"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={handleClearSearch}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
          <Button
            onClick={handleSearch}
            disabled={searchQuery.trim().length < 2}
            loading={searchLoading}
          >
            Szukaj
          </Button>
          {isSearchMode && (
            <Button variant="secondary" onClick={handleClearSearch}>
              Wyczyść
            </Button>
          )}
        </div>

        <Card>
          <CardHeader>
            <InvoiceFilters
              onFilter={handleFilter}
              onSync={handleSync}
              syncing={syncing}
              loading={displayLoading}
            />
          </CardHeader>
          <CardContent className="p-0">
            <InvoiceList
              invoices={displayInvoices}
              loading={displayLoading}
              totalCount={displayTotal}
              pageSize={pageSize}
              pageOffset={isSearchMode ? 0 : pageOffset}
              subjectType={currentSubjectType}
              onDownload={downloadInvoice}
              onNextPage={isSearchMode ? undefined : nextPage}
              onPrevPage={isSearchMode ? undefined : prevPage}
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
