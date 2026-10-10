import React from 'react';
import { Loader2, WifiOff, Database } from 'lucide-react';

interface LoadingStateProps {
  message?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({ message = 'Đang tải dữ liệu...' }) => (
  <div className="flex flex-col items-center justify-center h-40 gap-3 text-[var(--color-text-tertiary)]">
    <Loader2 className="w-6 h-6 animate-spin text-[var(--color-brand-primary)]" />
    <span className="text-sm">{message}</span>
  </div>
);

interface EmptyStateProps {
  message?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ message = 'Không có dữ liệu' }) => (
  <div className="flex flex-col items-center justify-center h-40 gap-3 text-[var(--color-text-tertiary)]">
    <Database className="w-8 h-8 opacity-40" />
    <span className="text-sm">{message}</span>
  </div>
);

interface ErrorStateProps {
  message?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({ message = 'Không thể tải dữ liệu. Vui lòng thử lại.' }) => (
  <div className="flex flex-col items-center justify-center h-40 gap-3">
    <WifiOff className="w-8 h-8 text-[var(--color-status-error)] opacity-60" />
    <span className="text-sm text-[var(--color-text-tertiary)]">{message}</span>
    <button
      className="px-3 py-1.5 text-xs border border-[var(--color-border)] rounded text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)] transition-colors"
    >
      Thử lại
    </button>
  </div>
);
