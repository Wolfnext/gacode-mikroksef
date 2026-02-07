'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import type { MonthlyTurnover } from '@/types/analytics';

interface MonthlyChartProps {
  data: MonthlyTurnover[];
}

export function MonthlyChart({ data }: MonthlyChartProps) {
  const chartData = [...data].reverse().map((m) => ({
    month: m.month,
    Wystawione: m.issuedGross,
    Otrzymane: m.receivedGross,
  }));

  if (chartData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Obrót miesięczny</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">
            Brak danych do wyświetlenia
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Obrót miesięczny</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" fontSize={12} />
            <YAxis fontSize={12} />
            <Tooltip
              formatter={(value: number) =>
                value.toLocaleString('pl-PL', { style: 'currency', currency: 'PLN' })
              }
            />
            <Legend />
            <Bar dataKey="Wystawione" fill="#2563eb" radius={[2, 2, 0, 0]} />
            <Bar dataKey="Otrzymane" fill="#16a34a" radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
