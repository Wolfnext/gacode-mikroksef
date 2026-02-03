'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import type { InvoiceQueryParams } from '@/types';
import { Search, RefreshCw, Filter } from 'lucide-react';

interface InvoiceFiltersProps {
  onFilter: (params: InvoiceQueryParams) => void;
  onSync: () => void;
  syncing: boolean;
  loading: boolean;
}

export function InvoiceFilters({ onFilter, onSync, syncing, loading }: InvoiceFiltersProps) {
  const [subjectType, setSubjectType] = useState<'subject1' | 'subject2'>('subject1');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [nipFilter, setNipFilter] = useState('');
  const [invoiceType, setInvoiceType] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  const handleApplyFilters = () => {
    const params: InvoiceQueryParams = {
      subjectType,
      pageOffset: 0,
    };

    if (dateFrom) params.dateFrom = dateFrom;
    if (dateTo) params.dateTo = dateTo;
    if (nipFilter) params.nipFilter = nipFilter;
    if (invoiceType) params.invoiceType = invoiceType;

    onFilter(params);
  };

  const handleClearFilters = () => {
    setDateFrom('');
    setDateTo('');
    setNipFilter('');
    setInvoiceType('');
    onFilter({ subjectType, pageOffset: 0 });
  };

  return (
    <div className="space-y-4">
      {/* Main filters row */}
      <div className="flex flex-wrap items-center gap-4">
        <Select
          value={subjectType}
          onChange={(e) => {
            setSubjectType(e.target.value as 'subject1' | 'subject2');
            onFilter({ subjectType: e.target.value as 'subject1' | 'subject2', pageOffset: 0 });
          }}
          className="w-40"
        >
          <option value="subject1">Wystawione</option>
          <option value="subject2">Otrzymane</option>
        </Select>

        <Button
          variant="secondary"
          onClick={() => setShowFilters(!showFilters)}
        >
          <Filter className="w-4 h-4 mr-2" />
          Filtry
        </Button>

        <Button
          variant="secondary"
          onClick={onSync}
          loading={syncing}
          disabled={loading}
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${syncing ? 'animate-spin' : ''}`} />
          Synchronizuj
        </Button>
      </div>

      {/* Extended filters */}
      {showFilters && (
        <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Input
              label="Data od"
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />

            <Input
              label="Data do"
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />

            <Input
              label="NIP kontrahenta"
              value={nipFilter}
              onChange={(e) => setNipFilter(e.target.value)}
              placeholder="1234567890"
            />

            <Select
              label="Typ faktury"
              value={invoiceType}
              onChange={(e) => setInvoiceType(e.target.value)}
            >
              <option value="">Wszystkie</option>
              <option value="VAT">Faktura VAT</option>
              <option value="KOR">Korekta</option>
              <option value="ZAL">Zaliczkowa</option>
              <option value="ROZ">Rozliczeniowa</option>
            </Select>
          </div>

          <div className="flex justify-end gap-2 mt-4">
            <Button variant="ghost" onClick={handleClearFilters}>
              Wyczyść
            </Button>
            <Button onClick={handleApplyFilters}>
              <Search className="w-4 h-4 mr-2" />
              Zastosuj filtry
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
