'use client';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { formatNip, getRelativeTime } from '@/lib/utils';
import type { SessionStatus as SessionStatusType } from '@/types';
import { LogOut, RefreshCw } from 'lucide-react';

interface SessionStatusProps {
  session: SessionStatusType | null;
  onRefresh: () => void;
  onLogout: () => void;
  loading: boolean;
}

export function SessionStatus({ session, onRefresh, onLogout, loading }: SessionStatusProps) {
  if (!session) {
    return (
      <div className="flex items-center gap-2">
        <Badge variant="danger">Brak sesji</Badge>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-4">
      <div className="flex items-center gap-2">
        <Badge variant={session.isActive ? 'success' : 'danger'}>
          {session.isActive ? 'Aktywna' : 'Nieaktywna'}
        </Badge>
        <span className="text-sm text-gray-600 dark:text-gray-400 hidden md:inline">
          Ref: {session.referenceNumber.slice(0, 12)}...
        </span>
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={onRefresh}
          disabled={loading}
          title="Odśwież status"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </Button>

        <Button
          variant="danger"
          size="sm"
          onClick={onLogout}
          disabled={loading}
        >
          <LogOut className="w-4 h-4 mr-1" />
          <span className="hidden sm:inline">Wyloguj</span>
        </Button>
      </div>
    </div>
  );
}
