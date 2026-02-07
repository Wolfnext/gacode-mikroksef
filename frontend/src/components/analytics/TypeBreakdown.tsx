'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import type { InvoiceTypeSummary } from '@/types/analytics';

const TYPE_LABELS: Record<string, string> = {
  VAT: 'Faktura VAT',
  KOR: 'Korekta',
  ZAL: 'Faktura zaliczkowa',
  ROZ: 'Faktura rozliczeniowa',
};

interface TypeBreakdownProps {
  data: InvoiceTypeSummary[];
}

function fmt(value: number): string {
  return value.toLocaleString('pl-PL', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function TypeBreakdown({ data }: TypeBreakdownProps) {
  if (data.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Podział wg typu faktury</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b dark:border-gray-700">
                <th className="text-left py-2 font-medium text-gray-600 dark:text-gray-400">Typ</th>
                <th className="text-right py-2 font-medium text-gray-600 dark:text-gray-400">Ilość</th>
                <th className="text-right py-2 font-medium text-gray-600 dark:text-gray-400">Netto</th>
                <th className="text-right py-2 font-medium text-gray-600 dark:text-gray-400">VAT</th>
                <th className="text-right py-2 font-medium text-gray-600 dark:text-gray-400">Brutto</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row) => (
                <tr key={row.invoiceType} className="border-b dark:border-gray-700">
                  <td className="py-2 text-gray-900 dark:text-gray-100">
                    {TYPE_LABELS[row.invoiceType] || row.invoiceType}
                  </td>
                  <td className="text-right py-2 text-gray-700 dark:text-gray-300">{row.count}</td>
                  <td className="text-right py-2 text-gray-700 dark:text-gray-300">{fmt(row.netTotal)}</td>
                  <td className="text-right py-2 text-gray-700 dark:text-gray-300">{fmt(row.vatTotal)}</td>
                  <td className="text-right py-2 font-medium text-gray-900 dark:text-gray-100">{fmt(row.grossTotal)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
