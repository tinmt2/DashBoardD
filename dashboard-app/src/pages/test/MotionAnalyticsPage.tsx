import React, { useState } from 'react';
import { useTestTaskContext } from '../../context/TestTaskContext';
import { motionApi } from '../../services/testApi/motionApi';
import type { MotionJobState } from '../../types/testEngine';

const MotionAnalyticsPage: React.FC = () => {
  
  
  const { tasks, startTask, clearTask } = useTestTaskContext();
  const task = tasks['motion'];
  const [preJobId, setPreJobId] = useState<string | null>(null);
  const jobId = task?.jobId || preJobId;
  const jobState = task as any as MotionJobState;
  const [error, setError] = useState('');
  const [columns, setColumns] = useState<string[]>([]);
  
  const [shopCol, setShopCol] = useState('');
  const [warningCol, setWarningCol] = useState('');

  const handleUpload = async (selectedFile: File) => {
    
    setError('');
    setPreJobId(null);
      clearTask('motion');
    
    setColumns([]);
    
    try {
      const res = await motionApi.uploadFile(selectedFile);
      if (res.success && res.data) {
        setPreJobId(res.data.job_id);
        setColumns(res.data.columns);
        
        // Auto-select defaults mimicking Legacy logic:
        // Shop is usually first column, Warning is usually index 4 or last
        if (res.data.columns.length > 0) {
            setShopCol(res.data.columns[0]);
        }
        if (res.data.columns.length > 4) {
            setWarningCol(res.data.columns[4]);
        } else if (res.data.columns.length > 0) {
            setWarningCol(res.data.columns[res.data.columns.length - 1]);
        }
      } else {
        setError(res.message || 'Lỗi tải file');
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi kết nối');
    }
  };

  const startAnalyze = async () => {
    if (!jobId) return;
    setError('');
    try {
      const res = await motionApi.analyzeData(jobId, shopCol, warningCol);
      if (res.success) {
        startTask('motion', jobId, { columns, shopCol, warningCol });
      } else {
        setError(res.message || 'Lỗi phân tích');
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi kết nối');
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-sm border border-gray-100 p-6">
      <h2 className="text-2xl font-semibold text-gray-700 mb-6">Motion Analytics</h2>
      
      <div className="flex flex-col gap-4 max-w-md mb-8">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Tải file Excel/CSV</label>
          <input 
            type="file" 
            accept=".csv, .xlsx, .xls"
            onChange={(e) => e.target.files && handleUpload(e.target.files[0])}
            className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
        </div>

        {columns.length > 0 && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Cột chứa tên Shop:</label>
              <select 
                value={shopCol}
                onChange={(e) => setShopCol(e.target.value)}
                className="w-full text-sm border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                {columns.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Cột chứa Cảnh Báo:</label>
              <select 
                value={warningCol}
                onChange={(e) => setWarningCol(e.target.value)}
                className="w-full text-sm border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                {columns.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            
            <button 
              onClick={startAnalyze}
              className="mt-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 font-medium transition-colors"
            >
              Bắt đầu Phân tích & Sắp xếp
            </button>
          </>
        )}
        
        {error && <div className="text-red-500 text-sm mt-2 font-medium">{error}</div>}
      </div>

      {/* Results Table */}
      {jobState && jobState.status === 'completed' && (jobState?.results || []).length > 0 && (
        <div className="flex-1 overflow-auto border border-gray-200 rounded-lg">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tên Shop</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Tổng lượt cảnh báo</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {(jobState?.results || []).map((r: any, i: number) => (
                <tr key={i} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{r.shop}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-center text-gray-900">{r.warning}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {jobState && jobState.status === 'completed' && (jobState?.results || []).length === 0 && (
        <div className="text-gray-500 text-center mt-4">Không có dữ liệu</div>
      )}
    </div>
  );
};

export default MotionAnalyticsPage;
