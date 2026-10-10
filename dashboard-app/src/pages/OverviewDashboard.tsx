import React, { useState, useEffect } from 'react';
import { GlassCard } from '../components/common/GlassCard';
import { fetchDashboardSummary } from '../services/fptShopApi';
import { fetchLongChauSummary } from '../services/longChauApi';
import { fetchVaccineSummary } from '../services/vaccineApi';
import { Store, Pill, ShieldPlus } from 'lucide-react';

const ChainErrorColumn = ({ 
  title, 
  errors, 
  Icon, 
  colorTheme 
}: { 
  title: string, 
  errors: any[], 
  Icon: React.ElementType,
  colorTheme: 'slate' | 'blue' | 'teal' 
}) => {
  const [expandedErrors, setExpandedErrors] = useState<Record<string, boolean>>({});
  const toggleError = (type: string) => setExpandedErrors(prev => ({ ...prev, [type]: !prev[type] }));

  const themeClasses = {
    slate: {
      wrapper: 'bg-slate-50/80 border-slate-200/80',
      headerIconBg: 'bg-slate-100 text-slate-700',
      badgeBg: 'bg-slate-100 text-slate-600',
      countText: 'text-slate-800'
    },
    blue: {
      wrapper: 'bg-blue-50/60 border-blue-200/70',
      headerIconBg: 'bg-blue-100 text-blue-700',
      badgeBg: 'bg-blue-50 text-blue-600',
      countText: 'text-blue-600'
    },
    teal: {
      wrapper: 'bg-teal-50/60 border-teal-200/70',
      headerIconBg: 'bg-teal-100 text-teal-700',
      badgeBg: 'bg-teal-50 text-teal-600',
      countText: 'text-teal-600'
    }
  };

  const theme = themeClasses[colorTheme];

  return (
    <div className={`flex flex-col p-5 md:p-6 rounded-2xl border ${theme.wrapper}`}>
      {/* Column Header */}
      <div className="flex items-center gap-3 mb-6 px-1">
        <h3 className="text-[16px] font-bold text-slate-800">{title}</h3>
      </div>

      {/* Error List */}
      <div className="flex flex-col">
        {!errors || errors.length === 0 ? (
          <div className="text-[13px] text-slate-400 italic py-4 text-center">
            Không có dữ liệu
          </div>
        ) : (
          errors.map((err: any, i: number) => {
            const errType = err.type || err.errorType;
            const isExpanded = expandedErrors[errType];
            return (
              <div key={i} className="flex flex-col py-3.5 border-b border-black/5 last:border-0 group">
                <div 
                  className="flex items-center justify-between cursor-pointer"
                  onClick={() => toggleError(errType)}
                >
                  <div className="flex items-center gap-3 overflow-hidden">
                    <div className={`shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-[12px] font-bold ${theme.badgeBg}`}>
                      {i + 1}
                    </div>
                    <span 
                      className={`text-[13.5px] font-medium truncate pr-2 transition-colors ${isExpanded ? 'text-blue-600' : 'text-slate-600 group-hover:text-slate-900'}`}
                      title={errType}
                    >
                      {errType || 'Lỗi không xác định'}
                    </span>
                  </div>
                  <div className={`shrink-0 text-[15px] font-black ${theme.countText}`}>
                    {err.count}
                  </div>
                </div>
                
                {isExpanded && err.employees && err.employees.length > 0 && (
                  <div className="mt-3 ml-9 p-3 bg-white rounded-lg border border-slate-100 shadow-sm grid grid-cols-1 gap-y-2">
                    {err.employees.map((emp: any, j: number) => (
                      <div key={j} className="flex justify-between items-center text-[12px]">
                        <span className="text-slate-600 font-medium truncate pr-2" title={emp.name}>{emp.name}</span>
                        <span className={`font-bold px-1.5 py-0.5 rounded ${theme.badgeBg}`}>{emp.count}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

const OverviewDashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
          const fetchData = async () => {
        setLoading(true);
        try {
          const endDate = new Date();
          const startDate = new Date();
          startDate.setDate(endDate.getDate() - 7);
          const syncStartDate = new Date(startDate.getTime() - startDate.getTimezoneOffset() * 60000).toISOString().split('T')[0];
          const syncEndDate = new Date(endDate.getTime() - endDate.getTimezoneOffset() * 60000).toISOString().split('T')[0];

          const [fpt, lc, vac] = await Promise.all([
            fetchDashboardSummary(syncStartDate, syncEndDate),
            fetchLongChauSummary(syncStartDate, syncEndDate),
            fetchVaccineSummary(syncStartDate, syncEndDate)
          ]);
        
        setData({
          fpt: fpt.errorTypeStats || [],
          lc: lc.data?.errorTypeStats || [],
          vac: vac.data?.errorTypeStats || []
        });
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };
          fetchData();
      
      const interval = setInterval(fetchData, 5 * 60 * 1000); // 5 minutes
      return () => clearInterval(interval);
    }, []);

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[60vh]">
        <div className="animate-pulse flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-4 border-slate-200 border-t-slate-800 rounded-full animate-spin"></div>
          <div className="text-slate-500 font-medium">Đang tải dữ liệu...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-[1400px] mx-auto space-y-8">
      
      {/* Unified Card for Error Types */}
      <GlassCard className="p-6 md:p-8">
        

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
          <ChainErrorColumn 
            title="FPT Shop" 
            errors={data?.fpt} 
            Icon={Store} 
            colorTheme="slate" 
          />
          <ChainErrorColumn 
            title="Long Châu" 
            errors={data?.lc} 
            Icon={Pill} 
            colorTheme="blue" 
          />
          <ChainErrorColumn 
            title="Vaccine" 
            errors={data?.vac} 
            Icon={ShieldPlus} 
            colorTheme="teal" 
          />
        </div>
      </GlassCard>

    </div>
  );
};

export default OverviewDashboard;
