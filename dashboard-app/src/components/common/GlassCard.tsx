import React from 'react';

export const GlassCard = ({ children, className = '' }: { children: React.ReactNode, className?: string }) => {
  return (
    <div className={className} style={{
      backgroundColor: 'rgba(255, 255, 255, 0.4)',
      backdropFilter: 'blur(40px) saturate(150%)',
      WebkitBackdropFilter: 'blur(40px) saturate(150%)',
      borderRadius: '24px',
      border: '1px solid rgba(255, 255, 255, 0.6)',
      boxShadow: '0 8px 32px rgba(0,0,0,0.06)'
    }}>
      {children}
    </div>
  );
};
