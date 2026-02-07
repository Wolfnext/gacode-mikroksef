'use client';

import { useState, FormEvent } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Alert } from '@/components/ui/Alert';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { cleanNip, isValidNip, formatNip } from '@/lib/utils';

interface LoginFormProps {
  onLogin: (nip: string) => Promise<boolean>;
  loading: boolean;
  error: string | null;
}

export function LoginForm({ onLogin, loading, error }: LoginFormProps) {
  const [nip, setNip] = useState('');
  const [nipError, setNipError] = useState<string | null>(null);

  const handleNipChange = (value: string) => {
    // Allow only digits and formatting characters
    const cleaned = value.replace(/[^\d\-\s]/g, '');
    setNip(cleaned);
    setNipError(null);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    const cleanedNip = cleanNip(nip);

    if (cleanedNip.length !== 10) {
      setNipError('NIP musi mieć 10 cyfr');
      return;
    }

    if (!isValidNip(cleanedNip)) {
      setNipError('Nieprawidłowy numer NIP');
      return;
    }

    await onLogin(cleanedNip);
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl">Zaloguj się do KSeF</CardTitle>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
          Wprowadź NIP firmy, aby rozpocząć sesję
        </p>
      </CardHeader>

      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="NIP"
            value={nip}
            onChange={(e) => handleNipChange(e.target.value)}
            placeholder="XXX-XXX-XX-XX"
            error={nipError || undefined}
            hint={`${cleanNip(nip).length}/10 cyfr`}
            maxLength={13}
            autoFocus
          />

          {error && (
            <Alert variant="error">
              {error}
            </Alert>
          )}

          <Button
            type="submit"
            className="w-full"
            loading={loading}
            disabled={cleanNip(nip).length !== 10}
          >
            Zaloguj
          </Button>
        </form>

      </CardContent>
    </Card>
  );
}
