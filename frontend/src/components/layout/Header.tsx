'use client';

import Link from 'next/link';
import { SessionStatus } from '@/components/auth/SessionStatus';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import type { SessionStatus as SessionStatusType } from '@/types';
import { FileText, Settings } from 'lucide-react';

interface HeaderProps {
  session: SessionStatusType | null;
  onRefresh: () => void;
  onLogout: () => void;
  loading: boolean;
}

export function Header({ session, onRefresh, onLogout, loading }: HeaderProps) {
  return (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-50 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Nav */}
          <div className="flex items-center gap-8">
            <Link href="/dashboard" className="flex items-center gap-2">
              <FileText className="w-8 h-8 text-primary-600 dark:text-primary-400" />
              <span className="text-xl font-bold text-gray-900 dark:text-white">mikroKSeF</span>
            </Link>

            {session?.isActive && (
              <nav className="hidden md:flex items-center gap-6">
                <Link
                  href="/dashboard"
                  className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
                >
                  Dashboard
                </Link>
                <Link
                  href="/invoices"
                  className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
                >
                  Faktury
                </Link>
                <Link
                  href="/settings"
                  className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white flex items-center"
                >
                  <Settings className="w-4 h-4 mr-1" />
                  Ustawienia
                </Link>
              </nav>
            )}
          </div>

          {/* Theme Toggle & Session Status */}
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <SessionStatus
              session={session}
              onRefresh={onRefresh}
              onLogout={onLogout}
              loading={loading}
            />
          </div>
        </div>
      </div>
    </header>
  );
}
