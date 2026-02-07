'use client';

import { Card, CardContent } from '@/components/ui/Card';
import type { AnalyticsSummary } from '@/types/analytics';

interface SummaryCardsProps {
  data: AnalyticsSummary;
}

function formatCurrency(value: number): string {
  return value.toLocaleString('pl-PL', { style: 'currency', currency: 'PLN' });
}

export function SummaryCards({ data }: SummaryCardsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <Card>
        <CardContent className="pt-6">
          <p className="text-sm text-gray-500 dark:text-gray-400">Sprzedaż (brutto)</p>
          <p className="text-2xl font-bold text-primary-600 dark:text-primary-400 mt-1">
            {formatCurrency(data.totalIssued)}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          <p className="text-sm text-gray-500 dark:text-gray-400">Zakupy (brutto)</p>
          <p className="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">
            {formatCurrency(data.totalReceived)}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          <p className="text-sm text-gray-500 dark:text-gray-400">Liczba faktur</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-1">
            {data.invoiceCount}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
