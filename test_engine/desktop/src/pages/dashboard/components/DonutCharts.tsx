// @ts-nocheck
import { useState } from 'react';
import { formatNumber, formatDecimal } from './utils';
import { dashboardMockData } from '../mockDashboardData';

export const StandardDonut = ({ data, size = 200, strokeWidth = 24, centerText, centerSubtext }: any) => {
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);
  
  const radius = (size - strokeWidth) / 2;
  const cx = size / 2;
  const cy = size / 2;
  const circumference = 2 * Math.PI * radius;
  
  const total = data.reduce((sum: number, item: any) => sum + item.count, 0);
  let currentOffset = 0;
  
  return (
    <div className="relative flex justify-center items-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90 overflow-visible">
        {data.map((item: any, idx: number) => {
          const pct = item.count / total;
          const dash = pct * circumference;
          const offset = currentOffset;
          currentOffset -= dash;
          
          const isHovered = hoverIdx === idx;
          return (
            <circle
              key={idx}
              cx={cx}
              cy={cy}
              r={radius}
              fill="transparent"
              stroke={item.color}
              strokeWidth={isHovered ? strokeWidth + 4 : strokeWidth}
              strokeDasharray={`${dash} ${circumference}`}
              strokeDashoffset={offset}
              className="transition-all duration-300 cursor-pointer"
              onMouseEnter={() => setHoverIdx(idx)}
              onMouseLeave={() => setHoverIdx(null)}
              pointerEvents="stroke"
            />
          );
        })}
      </svg>
      
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <span className="text-2xl font-light text-slate-200">{centerText}</span>
        <span className="text-[10px] uppercase tracking-widest text-slate-500 mt-1">{centerSubtext}</span>
      </div>
      
      {hoverIdx !== null && (
        <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-full bg-slate-800 text-white text-xs py-2 px-3 rounded-lg shadow-xl border border-slate-700 pointer-events-none z-50 whitespace-nowrap mb-2 transition-opacity">
          <div className="text-slate-400 mb-1 uppercase tracking-wider text-[10px]">{data[hoverIdx].label}</div>
          <div className="font-bold flex items-center">
             <span className="w-2 h-2 rounded-full mr-2" style={{ backgroundColor: data[hoverIdx].color }}></span>
             {formatNumber(data[hoverIdx].count)} {data[hoverIdx].unit || ''} ({formatDecimal((data[hoverIdx].count / total) * 100)}%)
          </div>
        </div>
      )}
    </div>
  );
};

export const CameraDonut = () => {
  const data = dashboardMockData.cameraStatus;
  const total = data.reduce((s, i) => s + i.count, 0);

  return (
    <div className="flex items-center justify-between">
      <StandardDonut data={data} centerText={formatNumber(total)} centerSubtext="Camera" />
      <div className="flex-1 ml-8 space-y-4">
        {data.map((item, idx) => (
          <div key={idx} className="flex items-center justify-between p-2 -mx-2 rounded-lg hover:bg-slate-800/30 transition-colors cursor-default">
            <div className="flex items-center">
              <span className="w-2.5 h-2.5 rounded-full mr-3" style={{ backgroundColor: item.color }}></span>
              <span className="text-sm text-slate-300">{item.label}</span>
            </div>
            <div className="flex space-x-6">
              <span className="text-sm font-medium text-slate-200 w-12 text-right">{formatNumber(item.count)}</span>
              <span className="text-sm text-slate-500 w-12 text-right">{formatDecimal((item.count/total)*100)}%</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export const JobsDonut = () => {
  const data = dashboardMockData.jobStatus;
  return (
    <div className="flex flex-col items-center">
      <StandardDonut data={data} size={110} strokeWidth={12} centerText="02" centerSubtext="Đang chạy" />
      <div className="mt-4 grid grid-cols-2 gap-x-6 gap-y-2 w-full text-[10px] uppercase tracking-wider font-semibold">
        {data.map((item, idx) => (
          <div key={idx} className="flex items-center justify-between">
            <span className="flex items-center text-slate-500">
              <span className="w-1.5 h-1.5 rounded-full mr-1.5" style={{ backgroundColor: item.color }}></span>
              {item.label}
            </span>
            <span className="text-slate-300">{item.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
