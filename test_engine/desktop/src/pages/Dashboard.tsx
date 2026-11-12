import React, { useState } from 'react';
import { dashboardMockData } from './dashboard/mockDashboardData';
import { formatNumber, formatDecimal } from './dashboard/components/utils';
import { Sparkline } from './dashboard/components/Sparkline';
import { CameraDonut, JobsDonut } from './dashboard/components/DonutCharts';
import { FlexibleChart } from './dashboard/components/FlexibleChart';

const Dashboard: React.FC = () => {
  const [timeFilter, setTimeFilter] = useState<'24h' | '7d' | '30d'>('24h');
  const d = dashboardMockData;

  return (
    <div className="bg-slate-950 min-h-screen text-slate-200 p-8 font-sans relative">
      
      {/* HEADER & FILTERS */}
      <header className="flex justify-between items-end mb-12">
        <div>
          <h1 className="text-3xl font-medium text-slate-100 tracking-tight mb-1">Tổng quan</h1>
          <p className="text-slate-500 text-sm">Chỉ số hệ thống và tình trạng vận hành</p>
        </div>
        <div className="flex space-x-2 bg-slate-900/50 p-1 rounded-lg border border-slate-800/50">
          <button 
            onClick={() => setTimeFilter('24h')}
            className={`px-4 py-1.5 text-sm rounded-md font-medium transition-colors ${timeFilter === '24h' ? 'text-emerald-400 bg-emerald-500/10' : 'text-slate-400 hover:text-slate-200'}`}
          >24 giờ</button>
          <button 
            onClick={() => setTimeFilter('7d')}
            className={`px-4 py-1.5 text-sm rounded-md font-medium transition-colors ${timeFilter === '7d' ? 'text-emerald-400 bg-emerald-500/10' : 'text-slate-400 hover:text-slate-200'}`}
          >7 ngày</button>
          <button 
            onClick={() => setTimeFilter('30d')}
            className={`px-4 py-1.5 text-sm rounded-md font-medium transition-colors ${timeFilter === '30d' ? 'text-emerald-400 bg-emerald-500/10' : 'text-slate-400 hover:text-slate-200'}`}
          >30 ngày</button>
        </div>
      </header>

      {/* KPI SUMMARY WITH MICRO DONUT */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-16 bg-slate-900/20 p-6 rounded-2xl border border-slate-800/40">
        
        {/* Total Cameras */}
        <div className="flex flex-col justify-between">
          <div className="flex justify-between items-start mb-2">
            <div className="text-xs uppercase tracking-widest text-slate-500 font-semibold">Tổng Camera</div>
            <div className={`text-xs font-semibold px-2 py-0.5 rounded flex items-center ${d.summary.cameraGrowth >= 0 ? 'text-emerald-500 bg-emerald-500/10' : 'text-red-400 bg-red-500/10'}`}>
              {d.summary.cameraGrowth >= 0 ? '↑' : '↓'} {Math.abs(d.summary.cameraGrowth)}%
            </div>
          </div>
          <div className="text-4xl font-light text-slate-100 mb-4">{formatNumber(d.summary.totalCameras)}</div>
          <Sparkline data={d.summary.totalCamerasTrend} color={d.summary.cameraGrowth >= 0 ? '#10b981' : '#f87171'} />
        </div>

        {/* Online Rate */}
        <div className="flex flex-col justify-between border-l border-slate-800/60 pl-8">
          <div className="flex justify-between items-start mb-2">
            <div className="text-xs uppercase tracking-widest text-slate-500 font-semibold">Tỷ lệ Online</div>
            <div className={`text-xs font-semibold px-2 py-0.5 rounded flex items-center ${d.summary.onlineGrowth >= 0 ? 'text-emerald-500 bg-emerald-500/10' : 'text-red-400 bg-red-500/10'}`}>
              {d.summary.onlineGrowth >= 0 ? '↑' : '↓'} {formatDecimal(Math.abs(d.summary.onlineGrowth))}%
            </div>
          </div>
          <div className="text-4xl font-light text-slate-100 mb-4">{formatDecimal(d.summary.onlineRate)}%</div>
          <Sparkline data={d.summary.onlineRateTrend} color={d.summary.onlineGrowth >= 0 ? '#10b981' : '#f87171'} />
        </div>

        {/* Errors */}
        <div className="flex flex-col justify-between border-l border-slate-800/60 pl-8">
          <div className="flex justify-between items-start mb-2">
            <div className="text-xs uppercase tracking-widest text-slate-500 font-semibold">Lỗi</div>
            <div className={`text-xs font-semibold px-2 py-0.5 rounded flex items-center ${d.summary.errorsGrowth <= 0 ? 'text-emerald-500 bg-emerald-500/10' : 'text-red-400 bg-red-500/10'}`}>
              {d.summary.errorsGrowth <= 0 ? '↓' : '↑'} {formatDecimal(Math.abs(d.summary.errorsGrowth))}%
            </div>
          </div>
          <div className="text-4xl font-light text-slate-100 mb-4">{formatNumber(d.summary.errors)}</div>
          <Sparkline data={d.summary.errorsTrend} color={d.summary.errorsGrowth <= 0 ? '#10b981' : '#f87171'} />
        </div>

        {/* Active Jobs Donut */}
        <div className="flex flex-col justify-between border-l border-slate-800/60 pl-8">
          <div className="text-xs uppercase tracking-widest text-slate-500 font-semibold mb-4">Phân bổ tác vụ</div>
          <JobsDonut />
        </div>
      </div>

      {/* PRIMARY CHART */}
      <div className="mb-16">
        <FlexibleChart data={d.errorTrend} />
      </div>

      {/* DONUT & REGIONAL ROW */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-16">
        
        {/* CAMERA STATUS DONUT */}
        <div>
          <h2 className="text-xs uppercase tracking-widest text-slate-500 font-semibold mb-6">Phân bổ trạng thái Camera</h2>
          <div className="bg-slate-900/30 border border-slate-800/40 rounded-2xl p-6 h-[340px] flex flex-col justify-center">
            <CameraDonut />
          </div>
        </div>

        {/* REGIONAL TABLE */}
        <div>
          <h2 className="text-xs uppercase tracking-widest text-slate-500 font-semibold mb-6">Tổng quan theo khu vực</h2>
          <div className="bg-slate-900/30 border border-slate-800/40 rounded-2xl p-6 h-[340px] overflow-hidden">
            <table className="w-full text-left">
              <thead>
                <tr className="text-[10px] uppercase tracking-widest text-slate-600 border-b border-slate-800/50">
                  <th className="pb-3 font-medium">Khu vực</th>
                  <th className="pb-3 font-medium">Số Shop</th>
                  <th className="pb-3 font-medium">Offline</th>
                  <th className="pb-3 font-medium">Xu hướng</th>
                  <th className="pb-3 font-medium text-right">Trạng thái</th>
                </tr>
              </thead>
              <tbody className="text-sm">
                {d.regions.map((region, idx) => (
                  <tr key={idx} className="border-b border-slate-800/30 hover:bg-slate-800/20 transition-colors">
                    <td className="py-4 text-slate-300">{region.name}</td>
                    <td className="py-4 text-slate-400">{formatNumber(region.shops)}</td>
                    <td className="py-4 text-slate-200">{formatNumber(region.offline)}</td>
                    <td className="py-4"><Sparkline data={region.trend} color={region.statusColor === 'amber' ? '#f59e0b' : region.statusColor === 'emerald' ? '#10b981' : '#f87171'} /></td>
                    <td className="py-4 text-right">
                      <span className={`px-2 py-1 rounded text-[10px] uppercase tracking-wider font-semibold ${region.statusColor === 'amber' ? 'text-amber-500 bg-amber-500/10' : region.statusColor === 'emerald' ? 'text-emerald-500 bg-emerald-500/10' : 'text-red-400 bg-red-500/10'}`}>
                        {region.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* DVR / FTEL + ACTIVE JOBS DETAILS */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
        
        {/* DVR */}
        <div>
          <h2 className="text-xs uppercase tracking-widest text-slate-500 font-semibold mb-6">Hạ tầng DVR</h2>
          <div className="bg-slate-900/30 border border-slate-800/40 rounded-2xl p-6">
             <div className="flex justify-between items-end mb-6">
               <div>
                 <div className="text-3xl font-light text-slate-200">{formatNumber(d.dvr.total)}</div>
                 <div className="text-sm text-slate-500 mt-1">Tổng thiết bị</div>
               </div>
               <div className="text-right">
                 <div className="text-3xl font-light text-amber-400">{formatNumber(d.dvr.errors)}</div>
                 <div className="text-sm text-slate-500 mt-1">Thiết bị có lỗi</div>
               </div>
             </div>
             
             <div className="mb-2 flex justify-between text-xs text-slate-400">
               <span>Online ({formatNumber(d.dvr.statusBreakdown.online)})</span>
               <span>Warning ({formatNumber(d.dvr.statusBreakdown.warning)})</span>
               <span>Lỗi ({formatNumber(d.dvr.statusBreakdown.error)})</span>
             </div>
             
             <div className="w-full h-2 rounded-full overflow-hidden flex mb-2">
               <div className="bg-emerald-500 h-full" style={{width: `${(d.dvr.statusBreakdown.online/d.dvr.total)*100}%`}}></div>
               <div className="bg-amber-400 h-full" style={{width: `${(d.dvr.statusBreakdown.warning/d.dvr.total)*100}%`}}></div>
               <div className="bg-red-400 h-full" style={{width: `${(d.dvr.statusBreakdown.error/d.dvr.total)*100}%`}}></div>
             </div>
          </div>
        </div>

        {/* ACTIVE JOBS DETAIL */}
        <div>
          <h2 className="text-xs uppercase tracking-widest text-slate-500 font-semibold mb-6">Chi tiết tác vụ</h2>
          <div className="bg-slate-900/30 border border-slate-800/40 rounded-2xl p-6 flex flex-col justify-center min-h-[148px]">
            <div className="space-y-4">
              {d.tasks.map((task, idx) => (
                <div key={idx}>
                  <div className="flex justify-between text-sm mb-2 text-slate-300">
                    <span>{task.name} {task.id}</span>
                    <span className="text-emerald-500 font-mono text-xs">{task.progress}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" style={{width: `${task.progress}%`, backgroundColor: task.color}}></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default Dashboard;
