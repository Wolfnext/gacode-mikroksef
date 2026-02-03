'use client';

import { HTMLAttributes, ReactNode } from 'react';
import { AlertCircle, CheckCircle, Info, XCircle } from 'lucide-react';

interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  children: ReactNode;
  onClose?: () => void;
}

export function Alert({
  variant = 'info',
  title,
  className = '',
  children,
  onClose,
  ...props
}: AlertProps) {
  const variants = {
    info: {
      container: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-800 dark:text-blue-200',
      icon: <Info className="w-5 h-5 text-blue-500 dark:text-blue-400" />,
    },
    success: {
      container: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 text-green-800 dark:text-green-200',
      icon: <CheckCircle className="w-5 h-5 text-green-500 dark:text-green-400" />,
    },
    warning: {
      container: 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800 text-yellow-800 dark:text-yellow-200',
      icon: <AlertCircle className="w-5 h-5 text-yellow-500 dark:text-yellow-400" />,
    },
    error: {
      container: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-800 dark:text-red-200',
      icon: <XCircle className="w-5 h-5 text-red-500 dark:text-red-400" />,
    },
  };

  const config = variants[variant];

  return (
    <div
      className={`rounded-md border p-4 ${config.container} ${className}`}
      role="alert"
      {...props}
    >
      <div className="flex">
        <div className="flex-shrink-0">{config.icon}</div>
        <div className="ml-3 flex-1">
          {title && <h3 className="text-sm font-medium">{title}</h3>}
          <div className={`text-sm ${title ? 'mt-1' : ''}`}>{children}</div>
        </div>
        {onClose && (
          <button
            type="button"
            className="ml-auto -mx-1.5 -my-1.5 rounded-lg p-1.5 inline-flex h-8 w-8 hover:bg-black/10"
            onClick={onClose}
          >
            <span className="sr-only">Zamknij</span>
            <XCircle className="w-5 h-5" />
          </button>
        )}
      </div>
    </div>
  );
}
