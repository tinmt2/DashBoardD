import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'success' | 'warning' | 'error' | 'info' | 'default';
  size?: 'sm' | 'md';
}

const variantClasses = {
  success: 'bg-green-950/60 text-green-400 border border-green-800/50',
  warning: 'bg-amber-950/60 text-amber-400 border border-amber-800/50',
  error: 'bg-red-950/60 text-red-400 border border-red-800/50',
  info: 'bg-blue-950/60 text-blue-400 border border-blue-800/50',
  default: 'bg-[var(--color-surface-active)] text-[var(--color-text-secondary)] border border-[var(--color-border)]',
};

const sizeClasses = {
  sm: 'text-[10px] px-1.5 py-0.5',
  md: 'text-xs px-2 py-1',
};

const Badge: React.FC<BadgeProps> = ({ children, variant = 'default', size = 'sm' }) => {
  return (
    <span className={`inline-flex items-center gap-1 rounded font-medium ${variantClasses[variant]} ${sizeClasses[size]}`}>
      {children}
    </span>
  );
};

export default Badge;
