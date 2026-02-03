'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { LoginForm } from '@/components/auth/LoginForm';
import { useAuth } from '@/hooks/useAuth';
import { FileText } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const { isAuthenticated, loading, error, login } = useAuth();

  useEffect(() => {
    if (!loading && isAuthenticated) {
      router.replace('/dashboard');
    }
  }, [loading, isAuthenticated, router]);

  const handleLogin = async (nip: string): Promise<boolean> => {
    const success = await login(nip);
    if (success) {
      router.push('/dashboard');
    }
    return success;
  };

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

      <footer className="mt-8 text-center text-xs text-gray-400 dark:text-gray-500">
        <p>Wersja 1.0.0</p>
        <p className="mt-1">Środowisko testowe KSeF</p>
      </footer>
    </main>
  );
}
