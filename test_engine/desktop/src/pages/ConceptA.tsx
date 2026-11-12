// @ts-nocheck
import React, { useState } from 'react';
import { 
  Activity, Camera, Server, AlertTriangle, CheckCircle, 
  TrendingUp, Clock, LayoutGrid, Ticket, BarChart3, 
  Layers, Map, RefreshCw, XCircle
} from 'lucide-react';

const mockData = {
  shops: 3374,
  cameras: 12482,
  online: 11856,
  offline: 426,
  newErrors: 38,
  existingErrors: 124,
  dvr: 3210,
  dvrErrors: 47,
  tickets: 86,
  jobs: 2
};

const SimpleBarChart = ({ data, color }: { data: number[], color: string }) => (
  <div className="flex items-end h-32 space-x-2">
    {data.map((v, i) => (
      <div key={i} className="flex-1 flex flex-col justify-end h-full">
        <div className={`w-full rounded-t-sm ${color} transition-all duration-500 hover:opacity-80`} style={{ height: `${v}%` }}></div>
      </div>
    ))}
  </div>
);

const ProgressBar = ({ progress, color }: { progress: number, color: string }) => (
  <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
    <div className={`h-full ${color}`} style={{ width: `${progress}%` }}></div>
  </div>
);

const KPICard = ({ title, value, icon, trend }: any) => (
  <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex flex-col justify-between hover:border-slate-700 cursor-pointer transition-colors">
    <div className="flex justify-between items-start mb-4">
      <div className="text-slate-400 font-medium text-sm">{title}</div>
      <div className="text-slate-500">{icon}</div>
    </div>
    <div>
      <div className="text-3xl font-bold text-slate-100">{value}</div>
      {trend && <div className={`text-xs mt-2 ${trend > 0 ? 'text-emerald-500' : 'text-red-500'}`}>{trend > 0 ? '↑' : '↓'} {Math.abs(trend)}% vs last week</div>}
    </div>
  </div>
);

export const ConceptA = () => {
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <KPICard title="Total Shops" value="3,374" icon={<Map className="w-5 h-5" />} trend={2.4} />
        <KPICard title="Cameras Online" value="11,856" icon={<Camera className="w-5 h-5" />} trend={0.8} />
        <KPICard title="Offline Cameras" value="426" icon={<AlertTriangle className="w-5 h-5" />} trend={-5.2} />
        <KPICard title="Open Tickets" value="86" icon={<Ticket className="w-5 h-5" />} trend={12} />
        <KPICard title="Active Jobs" value="2" icon={<RefreshCw className="w-5 h-5" />} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-slate-200 mb-6 flex items-center"><Activity className="w-5 h-5 mr-2 text-emerald-500" /> Error Trend (Last 7 Days)</h3>
          <SimpleBarChart data={[20, 35, 15, 60, 45, 80, mockData.existingErrors + mockData.newErrors]} color="bg-red-500/80" />
          <div className="flex justify-between mt-4 text-xs text-slate-500">
            <span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Today</span>
          </div>
        </div>
        
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-slate-200 mb-6 flex items-center"><Camera className="w-5 h-5 mr-2 text-emerald-500" /> Camera Health</h3>
          <div className="space-y-6">
            <div>
              <div className="flex justify-between text-sm mb-2"><span className="text-slate-300">Online ({mockData.online})</span><span className="text-emerald-500">95%</span></div>
              <ProgressBar progress={95} color="bg-emerald-500" />
            </div>
            <div>
              <div className="flex justify-between text-sm mb-2"><span className="text-slate-300">Offline ({mockData.offline})</span><span className="text-amber-500">3.4%</span></div>
              <ProgressBar progress={3.4} color="bg-amber-500" />
            </div>
            <div>
              <div className="flex justify-between text-sm mb-2"><span className="text-slate-300">Errors ({mockData.newErrors + mockData.existingErrors})</span><span className="text-red-500">1.6%</span></div>
              <ProgressBar progress={1.6} color="bg-red-500" />
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-slate-200 mb-4 flex items-center"><LayoutGrid className="w-5 h-5 mr-2 text-emerald-500" /> Regional Overview</h3>
          <table className="w-full text-left text-sm">
            <thead className="text-slate-400 border-b border-slate-800">
              <tr><th className="pb-3">Region</th><th className="pb-3">Shops</th><th className="pb-3">Offline</th><th className="pb-3">Status</th></tr>
            </thead>
            <tbody className="text-slate-200">
              <tr className="border-b border-slate-800/50"><td className="py-3">North</td><td className="py-3">1,240</td><td className="py-3 text-red-400">156</td><td className="py-3"><span className="px-2 py-1 bg-amber-500/20 text-amber-500 rounded text-xs">Warning</span></td></tr>
              <tr className="border-b border-slate-800/50"><td className="py-3">Central</td><td className="py-3">850</td><td className="py-3 text-red-400">42</td><td className="py-3"><span className="px-2 py-1 bg-emerald-500/20 text-emerald-500 rounded text-xs">Healthy</span></td></tr>
              <tr className="border-b border-slate-800/50"><td className="py-3">South</td><td className="py-3">1,284</td><td className="py-3 text-red-400">228</td><td className="py-3"><span className="px-2 py-1 bg-red-500/20 text-red-500 rounded text-xs">Critical</span></td></tr>
            </tbody>
          </table>
        </div>
        
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-slate-200 mb-4 flex items-center"><Server className="w-5 h-5 mr-2 text-emerald-500" /> DVR & Infrastructure</h3>
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="p-4 bg-slate-950 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-sm mb-1">Total DVRs</div>
              <div className="text-2xl font-bold text-slate-100">{mockData.dvr}</div>
            </div>
            <div className="p-4 bg-slate-950 rounded-lg border border-slate-800">
              <div className="text-slate-400 text-sm mb-1">DVR Errors</div>
              <div className="text-2xl font-bold text-red-400">{mockData.dvrErrors}</div>
            </div>
          </div>
          <h4 className="text-sm font-medium text-slate-400 mb-3">Active Jobs</h4>
          <div className="space-y-4">
            <div className="bg-slate-800/30 p-3 rounded-lg border border-slate-800">
              <div className="flex justify-between text-sm mb-2 text-slate-300"><span>Camera Scan #884</span><span className="text-emerald-500">Running (82%)</span></div>
              <ProgressBar progress={82} color="bg-emerald-500" />
            </div>
            <div className="bg-slate-800/30 p-3 rounded-lg border border-slate-800">
              <div className="flex justify-between text-sm mb-2 text-slate-300"><span>DVR Check #112</span><span className="text-emerald-500">Running (45%)</span></div>
              <ProgressBar progress={45} color="bg-emerald-500" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
