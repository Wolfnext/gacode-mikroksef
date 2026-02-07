'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { LoginForm } from '@/components/auth/LoginForm';
import { useAuth } from '@/hooks/useAuth';
import { healthApi } from '@/lib/api';
import { FileText, Server } from 'lucide-react';

const ENV_LABELS: Record<string, string> = {
  production: 'Środowisko produkcyjne',
  test: 'Środowisko testowe',
  demo: 'Środowisko demo',
};

export default function LoginPage() {
  const router = useRouter();
  const { isAuthenticated, loading, error, login } = useAuth();
  const [envInfo, setEnvInfo] = useState<{ environment: string; ksefApi: string } | null>(null);

  useEffect(() => {
    if (!loading && isAuthenticated) {
      router.replace('/dashboard');
    }
  }, [loading, isAuthenticated, router]);

  useEffect(() => {
    healthApi.check().then(({ data }) => {
      if (data) {
        setEnvInfo({
          environment: data.environment,
          ksefApi: data.ksefApi,
        });
      }
    });
  }, []);

  const handleLogin = async (nip: string): Promise<boolean> => {
    const success = await login(nip);
    if (success) {
      router.push('/dashboard');
    }
    return success;
  };

  const isProduction = envInfo?.environment === 'production';
  const ksefHost = envInfo?.ksefApi ? new URL(envInfo.ksefApi).hostname : '';

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-4 bg-gradient-to-b from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <div className="mb-8 text-center">
        <div className="flex items-center justify-center gap-3 mb-2">
          <FileText className="w-12 h-12 text-primary-600 dark:text-primary-400" />
          <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100">mikroKSeF</h1>
        </div>
        <p className="text-gray-600 dark:text-gray-400">Lokalny klient Krajowego Systemu e-Faktur</p>
      </div>

      <LoginForm onLogin={handleLogin} loading={loading} error={error} />

      {envInfo && (
        <div className={`mt-6 px-4 py-3 rounded-lg border text-center text-sm ${
          isProduction
            ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 text-green-700 dark:text-green-400'
            : 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-400'
        }`}>
          <div className="flex items-center justify-center gap-2 mb-1">
            <Server className="w-4 h-4" />
            <span className="font-medium">
              Połączenie z: {ksefHost}
            </span>
          </div>
          <p className="text-xs opacity-75">
            {ENV_LABELS[envInfo.environment] || envInfo.environment}
          </p>
        </div>
      )}

      <footer className="mt-6 text-center text-xs text-gray-400 dark:text-gray-500">
        <p>Wersja 1.0.0</p>
      </footer>
    </main>
  );
}
