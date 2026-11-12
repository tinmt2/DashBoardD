// @ts-nocheck
import { useEffect, useState, useRef } from 'react';
import { generateSmoothPath } from './utils';

export const Sparkline = ({ data, color }: { data: number[], color: string }) => {
  const height = 24;
  const width = 80;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const points = data.map((v, i) => [
    (i / (data.length - 1)) * width,
    height - ((v - min) / range) * height
  ] as [number, number]);
  
  const pathD = generateSmoothPath(points, 0.2);
  return (
    <svg width={width} height={height} className="overflow-visible">
      <path d={pathD} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
};
