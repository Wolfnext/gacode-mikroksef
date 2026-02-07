'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';
import { Spinner } from '@/components/ui/Spinner';
import { useAuth } from '@/hooks/useAuth';
import { notificationsApi } from '@/lib/api';
import type { NotificationConfig, NotificationHistoryEntry } from '@/types/analytics';
import { Bell, Webhook, Mail, Send, History, CheckCircle, XCircle } from 'lucide-react';

export default function SettingsPage() {
  const router = useRouter();
  const { isAuthenticated, sessionStatus, loading: authLoading, logout, refresh } = useAuth();

  const [config, setConfig] = useState<NotificationConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [history, setHistory] = useState<NotificationHistoryEntry[]>([]);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (isAuthenticated) {
      notificationsApi.getConfig().then(({ data }) => {
        if (data) setConfig(data);
        setLoading(false);
      });
      notificationsApi.getHistory().then(({ data }) => {
        if (data) setHistory(data);
      });
    }
  }, [isAuthenticated]);

  const handleSave = async () => {
    if (!config) return;
    setSaving(true);
    setError('');
    setSuccess('');
    const { data, error: err } = await notificationsApi.updateConfig(config);
    if (data) {
      setConfig(data);
      setSuccess('Konfiguracja zapisana');
    } else {
      setError(err || 'Nie udało się zapisać konfiguracji');
    }
    setSaving(false);
  };

  const handleTest = async () => {
    setTesting(true);
    setError('');
    setSuccess('');
    const { error: err } = await notificationsApi.test();
    if (err) {
      setError(err);
    } else {
      setSuccess('Powiadomienie testowe wysłane');
      // Refresh history
      const { data } = await notificationsApi.getHistory();
      if (data) setHistory(data);
    }
    setTesting(false);
  };

  if (authLoading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <Spinner size="lg" />
      </main>
    );
  }

  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header
        session={sessionStatus}
        onRefresh={refresh}
        onLogout={logout}
        loading={authLoading}
      />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Ustawienia</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Konfiguracja powiadomień o nowych fakturach
          </p>
        </div>

        {success && (
          <Alert variant="success" className="mb-6" onClose={() => setSuccess('')}>
            {success}
          </Alert>
        )}
        {error && (
          <Alert variant="error" className="mb-6" onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        {loading ? (
          <div className="flex justify-center py-12">
            <Spinner size="lg" />
          </div>
        ) : config ? (
          <div className="space-y-6">
            {/* General */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bell className="w-5 h-5 text-primary-600" />
                  Powiadomienia
                </CardTitle>
              </CardHeader>
              <CardContent>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={config.enabled}
                    onChange={(e) => setConfig({ ...config, enabled: e.target.checked })}
                    className="w-4 h-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    Włącz powiadomienia o nowych fakturach
                  </span>
                </label>
              </CardContent>
            </Card>

            {/* Webhook */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Webhook className="w-5 h-5 text-blue-600" />
                  Webhook
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={config.webhookEnabled}
                      onChange={(e) => setConfig({ ...config, webhookEnabled: e.target.checked })}
                      className="w-4 h-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      Włącz webhook
                    </span>
                  </label>
                  {config.webhookEnabled && (
                    <Input
                      label="URL webhook"
                      type="url"
                      value={config.webhookUrl || ''}
                      onChange={(e) => setConfig({ ...config, webhookUrl: e.target.value })}
                      placeholder="https://example.com/webhook"
                    />
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Email */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Mail className="w-5 h-5 text-green-600" />
                  E-mail
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={config.emailEnabled}
                      onChange={(e) => setConfig({ ...config, emailEnabled: e.target.checked })}
                      className="w-4 h-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      Włącz powiadomienia e-mail
                    </span>
                  </label>
                  {config.emailEnabled && (
                    <div className="space-y-3">
                      <Input
                        label="Adres e-mail odbiorcy"
                        type="email"
                        value={config.emailTo || ''}
                        onChange={(e) => setConfig({ ...config, emailTo: e.target.value })}
                        placeholder="admin@example.com"
                      />
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <Input
                          label="SMTP Host"
                          value={config.smtpHost || ''}
                          onChange={(e) => setConfig({ ...config, smtpHost: e.target.value })}
                          placeholder="smtp.gmail.com"
                        />
                        <Input
                          label="SMTP Port"
                          type="number"
                          value={String(config.smtpPort || 587)}
                          onChange={(e) => setConfig({ ...config, smtpPort: parseInt(e.target.value) || 587 })}
                        />
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <Input
                          label="SMTP Użytkownik"
                          value={config.smtpUsername || ''}
                          onChange={(e) => setConfig({ ...config, smtpUsername: e.target.value })}
                        />
                        <Input
                          label="SMTP Hasło"
                          type="password"
                          value={config.smtpPassword || ''}
                          onChange={(e) => setConfig({ ...config, smtpPassword: e.target.value })}
                        />
                      </div>
                      <label className="flex items-center gap-3 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={config.smtpUseTls}
                          onChange={(e) => setConfig({ ...config, smtpUseTls: e.target.checked })}
                          className="w-4 h-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                        />
                        <span className="text-sm text-gray-700 dark:text-gray-300">
                          Użyj TLS
                        </span>
                      </label>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Actions */}
            <div className="flex gap-3">
              <Button onClick={handleSave} loading={saving}>
                Zapisz konfigurację
              </Button>
              <Button variant="secondary" onClick={handleTest} loading={testing}>
                <Send className="w-4 h-4 mr-2" />
                Wyślij test
              </Button>
            </div>

            {/* History */}
            {history.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <History className="w-5 h-5 text-gray-600" />
                    Historia powiadomień
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-200 dark:border-gray-700">
                          <th className="text-left px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Typ</th>
                          <th className="text-left px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Zdarzenie</th>
                          <th className="text-left px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Status</th>
                          <th className="text-left px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Data</th>
                        </tr>
                      </thead>
                      <tbody>
                        {history.map((entry) => (
                          <tr key={entry.id} className="border-b border-gray-100 dark:border-gray-800">
                            <td className="px-4 py-3 text-gray-700 dark:text-gray-300">
                              {entry.notificationType === 'webhook' ? (
                                <span className="flex items-center gap-1"><Webhook className="w-3 h-3" /> Webhook</span>
                              ) : (
                                <span className="flex items-center gap-1"><Mail className="w-3 h-3" /> E-mail</span>
                              )}
                            </td>
                            <td className="px-4 py-3 text-gray-700 dark:text-gray-300">{entry.triggerEvent}</td>
                            <td className="px-4 py-3">
                              {entry.status === 'sent' ? (
                                <span className="flex items-center gap-1 text-green-600"><CheckCircle className="w-3 h-3" /> Wysłano</span>
                              ) : (
                                <span className="flex items-center gap-1 text-red-600" title={entry.errorMessage}>
                                  <XCircle className="w-3 h-3" /> Błąd
                                </span>
                              )}
                            </td>
                            <td className="px-4 py-3 text-gray-500 dark:text-gray-400">
                              {new Date(entry.createdAt).toLocaleString('pl-PL')}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        ) : (
          <Alert variant="info">Nie udało się załadować konfiguracji powiadomień.</Alert>
        )}
      </main>
    </div>
  );
}
