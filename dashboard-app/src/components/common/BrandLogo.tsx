import React from 'react';

interface BrandLogoProps {
  size?: number | string;
  className?: string;
}

export const BrandLogo: React.FC<BrandLogoProps> = ({ size = 24, className = '' }) => {
  return (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      viewBox="0 0 64 64" 
      width={size} 
      height={size} 
      fill="none" 
      className={className}
    >
      <defs>
        <linearGradient id="brand-bg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#0a0e1a" />
          <stop offset="100%" stopColor="#18153b" />
        </linearGradient>
        <linearGradient id="brand-border" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.85" />
          <stop offset="50%" stopColor="#818cf8" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#c084fc" stopOpacity="0.85" />
        </linearGradient>
        <linearGradient id="brand-stem" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#38bdf8" />
          <stop offset="50%" stopColor="#3b82f6" />
          <stop offset="100%" stopColor="#6366f1" />
        </linearGradient>
        <linearGradient id="brand-loop" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#00f2fe" />
          <stop offset="35%" stopColor="#38bdf8" />
          <stop offset="70%" stopColor="#6366f1" />
          <stop offset="100%" stopColor="#a855f7" />
        </linearGradient>
        <radialGradient id="brand-pulse" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#34d399" />
          <stop offset="100%" stopColor="#059669" />
        </radialGradient>
      </defs>

      {/* High-contrast dark squircle tile */}
      <rect x="2.5" y="2.5" width="59" height="59" rx="15" fill="url(#brand-bg)" stroke="url(#brand-border)" strokeWidth="1.8" />

      {/* D Monogram Structure */}
      <g>
        {/* Outer Arc of D */}
        <path 
          d="M26 16 H36 C46.5 16 53 23 53 32 C53 41 46.5 48 36 48 H26" 
          stroke="url(#brand-loop)" 
          strokeWidth="6.8" 
          strokeLinecap="round" 
          strokeLinejoin="round" 
        />
        {/* Vertical Spine of D */}
        <path 
          d="M20 16 V48" 
          stroke="url(#brand-stem)" 
          strokeWidth="6.8" 
          strokeLinecap="round" 
        />
        {/* Realtime Pulse Radar Core */}
        <circle cx="36" cy="32" r="3.6" fill="url(#brand-pulse)" />
        <circle cx="36" cy="32" r="6.6" stroke="#34d399" strokeWidth="1.2" strokeOpacity="0.75" strokeDasharray="2 2" />
      </g>
    </svg>
  );
};

export default BrandLogo;
