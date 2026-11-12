// @ts-nocheck
import { useState } from 'react';
import { generateSmoothPath } from './utils';

export const FlexibleChart = ({ data, height = 280, showGrid = true }: any) => {
  const [chartType, setChartType] = useState<'line' | 'area' | 'column' | 'stacked'>('area');
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);
  
  const width = 800;
  const paddingX = 20;
  const paddingY = 20;
  
  const maxTotal = Math.max(...data.map((d: any) => d.new + d.resolved)) * 1.1;
  const maxSingle = Math.max(...data.map((d: any) => Math.max(d.new, d.resolved))) * 1.1;
  const currentMax = chartType === 'stacked' ? maxTotal : maxSingle;
  const min = 0;
  const range = currentMax - min;
  
  const getX = (i: number) => paddingX + (i / (data.length - 1)) * (width - paddingX * 2);
  const getY = (val: number) => height - paddingY - ((val - min) / range) * (height - paddingY * 2);

  const newPoints = data.map((d: any, i: number) => [getX(i), getY(d.new)] as [number, number]);
  const resolvedPoints = data.map((d: any, i: number) => [getX(i), getY(d.resolved)] as [number, number]);
  
  const newPath = generateSmoothPath(newPoints, 0.15);
  const resolvedPath = generateSmoothPath(resolvedPoints, 0.15);
  
  const newArea = `${newPath} L ${getX(data.length - 1)},${height - paddingY} L ${getX(0)},${height - paddingY} Z`;
  const resolvedArea = `${resolvedPath} L ${getX(data.length - 1)},${height - paddingY} L ${getX(0)},${height - paddingY} Z`;

  const colWidth = (width - paddingX * 2) / data.length * 0.4;

  return (
    <div className="w-full relative bg-slate-900/20 rounded-2xl p-6 border border-slate-800/40">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-xs uppercase tracking-widest text-slate-500 font-semibold mb-1">Diễn biến lỗi</h2>
          <div className="flex items-baseline space-x-3">
            <span className="text-3xl font-light text-slate-200">104</span>
            <span className="text-sm text-emerald-500">↓ 12,4% so với kỳ trước</span>
          </div>
        </div>
        
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-4 text-xs text-slate-500">
            <div className="flex items-center"><span className="w-2 h-2 rounded-full bg-red-400 mr-2"></span> Lỗi hệ thống</div>
            <div className="flex items-center"><span className="w-2 h-2 rounded-full bg-emerald-400 mr-2"></span> Đã xử lý</div>
          </div>
          
          <div className="flex bg-slate-900/50 p-1 rounded-lg border border-slate-800/50">
            {[
              { id: 'line', label: 'Đường' },
              { id: 'area', label: 'Vùng' },
              { id: 'column', label: 'Cột' },
              { id: 'stacked', label: 'Cột chồng' }
            ].map(type => (
              <button 
                key={type.id}
                onClick={() => setChartType(type.id as any)}
                className={`px-3 py-1 text-[11px] uppercase tracking-wider rounded-md font-medium transition-colors ${chartType === type.id ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-slate-200'}`}
              >
                {type.label}
              </button>
            ))}
          </div>
        </div>
      </div>
      
      <div className="relative w-full" style={{ height: `${height}px` }}>
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full overflow-visible preserve-3d" preserveAspectRatio="none">
          <defs>
            <linearGradient id="grad-red" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f87171" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#f87171" stopOpacity="0.0" />
            </linearGradient>
            <linearGradient id="grad-emerald" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {showGrid && (
            <g className="opacity-10">
              {[0, 0.25, 0.5, 0.75, 1].map(pct => (
                <line key={pct} x1={paddingX} y1={paddingY + (height - paddingY*2) * pct} x2={width - paddingX} y2={paddingY + (height - paddingY*2) * pct} stroke="currentColor" strokeWidth="1" strokeDasharray="4 4" />
              ))}
            </g>
          )}

          {chartType === 'area' && (
            <g>
              <path d={resolvedArea} fill="url(#grad-emerald)" />
              <path d={newArea} fill="url(#grad-red)" />
            </g>
          )}

          {(chartType === 'line' || chartType === 'area') && (
            <g>
              <path d={resolvedPath} fill="none" stroke="#10b981" strokeWidth="2.5" className="drop-shadow-sm opacity-60" strokeLinecap="round" strokeLinejoin="round" />
              <path d={newPath} fill="none" stroke="#f87171" strokeWidth="2.5" className="drop-shadow-md" strokeLinecap="round" strokeLinejoin="round" />
            </g>
          )}

          {chartType === 'column' && (
            <g>
              {data.map((d: any, i: number) => {
                const x = getX(i);
                const cw = colWidth / 2.2;
                const hNew = (height - paddingY) - getY(d.new);
                const hRes = (height - paddingY) - getY(d.resolved);
                return (
                  <g key={`col-${i}`}>
                    <rect x={x - cw - 2} y={getY(d.resolved)} width={cw} height={hRes} rx={cw/2} fill="#10b981" opacity={hoverIdx === i || hoverIdx === null ? 0.8 : 0.3} className="transition-opacity duration-200" />
                    <rect x={x + 2} y={getY(d.new)} width={cw} height={hNew} rx={cw/2} fill="#f87171" opacity={hoverIdx === i || hoverIdx === null ? 1 : 0.4} className="transition-opacity duration-200" />
                  </g>
                );
              })}
            </g>
          )}

          {chartType === 'stacked' && (
            <g>
              {data.map((d: any, i: number) => {
                const x = getX(i);
                const cw = colWidth;
                const hRes = (height - paddingY) - getY(d.resolved);
                const hNew = (height - paddingY) - getY(d.new);
                const yRes = getY(d.resolved);
                const yNew = yRes - hNew;
                return (
                  <g key={`stk-${i}`}>
                    <rect x={x - cw/2} y={yRes} width={cw} height={hRes} rx={4} fill="#10b981" opacity={hoverIdx === i || hoverIdx === null ? 0.7 : 0.3} className="transition-opacity duration-200" />
                    <rect x={x - cw/2} y={yNew} width={cw} height={hNew + 4} rx={4} fill="#f87171" opacity={hoverIdx === i || hoverIdx === null ? 1 : 0.4} className="transition-opacity duration-200" />
                  </g>
                );
              })}
            </g>
          )}

          {data.map((d: any, i: number) => {
            const x = getX(i);
            const segmentWidth = (width - paddingX * 2) / data.length;
            return (
              <g key={`hover-${i}`}>
                {(chartType === 'line' || chartType === 'area') && hoverIdx === i && (
                  <>
                    <circle cx={x} cy={getY(d.resolved)} r="5" fill="#10b981" className="shadow-lg" />
                    <circle cx={x} cy={getY(d.new)} r="5" fill="#f87171" className="shadow-lg" />
                    <line x1={x} y1={paddingY} x2={x} y2={height - paddingY} stroke="rgba(255,255,255,0.15)" strokeWidth="1" strokeDasharray="4 4" pointerEvents="none" />
                  </>
                )}
                <rect 
                  x={x - segmentWidth/2} 
                  y={0} 
                  width={segmentWidth} 
                  height={height} 
                  fill="transparent" 
                  onMouseEnter={() => setHoverIdx(i)}
                  onMouseLeave={() => setHoverIdx(null)}
                  className="cursor-crosshair"
                />
              </g>
            );
          })}
        </svg>
        
        {hoverIdx !== null && (
          <div 
            className="absolute top-0 transform -translate-x-1/2 -translate-y-full bg-slate-800 text-white text-xs py-2 px-3 rounded-lg shadow-xl border border-slate-700 pointer-events-none transition-all duration-100 z-50 whitespace-nowrap"
            style={{ left: `${(hoverIdx / (data.length - 1)) * 100}%`, marginTop: '10px' }}
          >
            <div className="text-slate-400 mb-2 font-medium">{data[hoverIdx].label}</div>
            <div className="flex flex-col space-y-1">
              <div className="font-bold flex items-center justify-between space-x-4">
                <span className="flex items-center"><span className="w-2 h-2 rounded-full mr-2 bg-red-400"></span> Lỗi hệ thống</span>
                <span>{data[hoverIdx].new}</span>
              </div>
              <div className="font-bold flex items-center justify-between space-x-4">
                <span className="flex items-center"><span className="w-2 h-2 rounded-full mr-2 bg-emerald-400"></span> Đã xử lý</span>
                <span>{data[hoverIdx].resolved}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="flex justify-between text-[10px] uppercase tracking-wider text-slate-600 mt-4 px-4">
         {data.map((d: any, i: number) => (
           <span key={i} className={hoverIdx === i ? 'text-slate-300' : ''}>{d.label}</span>
         ))}
      </div>
    </div>
  );
};
