import React, { useState, useEffect } from 'react';
import { settingsApi } from '../api/settings';
import type { AppSettings } from '../api/settings';

const Settings: React.FC = () => {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [warehouseFile, setWarehouseFile] = useState('');
  const [periodicEnabled, setPeriodicEnabled] = useState(false);
  const [periodicInterval, setPeriodicInterval] = useState(15);
  const [periodicAutoSync, setPeriodicAutoSync] = useState(true);
  const [recoverySheetName, setRecoverySheetName] = useState('Cam chập chờn');
  const [avatarUrl, setAvatarUrl] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    loadSettings();
    const savedAvatar = localStorage.getItem('userAvatar');
    if (savedAvatar) {
      setAvatarUrl(savedAvatar);
    }
  }, []);

  const loadSettings = async () => {
    try {
      const res = await settingsApi.getSettings();
      if (res.success && res.data) {
        setSettings(res.data);
        setWarehouseFile(res.data.paths?.warehouse_file || '');
        setPeriodicEnabled(res.data.check_cam?.periodic_enabled ?? false);
        setPeriodicInterval(res.data.check_cam?.periodic_interval_minutes ?? 15);
        setPeriodicAutoSync(res.data.check_cam?.periodic_auto_sync ?? true);
        setRecoverySheetName(res.data.check_cam?.recovery_sheet_name || 'Cam chập chờn');
      } else {
        setError(res.message || 'Lỗi tải cấu hình');
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi kết nối Backend');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage('');
    setError('');
    try {
      const payload = {
        paths: {
          warehouse_file: warehouseFile
        },
        check_cam: {
          periodic_enabled: periodicEnabled,
          periodic_interval_minutes: Number(periodicInterval) || 15,
          periodic_auto_sync: periodicAutoSync,
          recovery_sheet_name: recoverySheetName.trim() || 'Cam chập chờn'
        }
      };
      const res = await settingsApi.updateSettings(payload);
      if (res.success) {
        if (avatarUrl) {
          localStorage.setItem('userAvatar', avatarUrl);
        } else {
          localStorage.removeItem('userAvatar');
        }
        window.dispatchEvent(new Event('avatarChanged'));
        
        setMessage('Đã cập nhật cấu hình thành công!');
        // Reload to ensure parity
        loadSettings();
      } else {
        setError(res.message || 'Lỗi lưu cấu hình');
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi kết nối Backend');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-gray-500">Đang tải cấu hình...</div>;
  }

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-sm border border-gray-100 p-6">
      <h2 className="text-2xl font-semibold text-gray-700 mb-6">Cập nhật Dữ liệu / Settings</h2>
      
      <div className="max-w-xl flex flex-col gap-6">
        
        {/* Vùng miền */}
        <div className="border border-gray-200 rounded-lg p-5 bg-gray-50">
          <h3 className="font-semibold text-gray-700 mb-2">Danh sách Vùng miền (Google Sheets)</h3>
          <p className="text-sm font-medium text-blue-500">
            Tự động tải từ tab 'Phân công' trên Google Sheet (Cột G-I)
          </p>
          {settings?.gsheet?.configured && (
            <p className="text-xs text-gray-400 mt-2">
              (GSheet ID: {settings.gsheet.spreadsheet_id})
            </p>
          )}
        </div>

        {/* Avatar */}
        <div className="border border-gray-200 rounded-lg p-5">
          <h3 className="font-semibold text-gray-700 mb-4">Ảnh đại diện (Avatar)</h3>
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-slate-200 flex items-center justify-center overflow-hidden border border-gray-300">
              {avatarUrl ? (
                <img src={avatarUrl} alt="Avatar" className="w-full h-full object-cover" />
              ) : (
                <span className="text-gray-500 font-bold text-xl">T</span>
              )}
            </div>
            <label className="cursor-pointer px-4 py-2 bg-gray-100 border border-gray-300 rounded-md text-sm font-medium hover:bg-gray-200 text-gray-700">
              Chọn Ảnh
              <input 
                type="file" 
                className="hidden" 
                accept="image/png, image/jpeg, image/jpg"
                onChange={(e) => {
                  if (e.target.files && e.target.files.length > 0) {
                    const file = e.target.files[0];
                    const reader = new FileReader();
                    reader.onload = (event) => {
                      if (event.target?.result) {
                        setAvatarUrl(event.target.result as string);
                      }
                    };
                    reader.readAsDataURL(file);
                  }
                }}
              />
            </label>
            {avatarUrl && (
              <button
                onClick={() => setAvatarUrl('')}
                className="px-4 py-2 text-red-600 border border-red-200 rounded-md text-sm font-medium hover:bg-red-50"
              >
                Xóa
              </button>
            )}
          </div>
        </div>

        {/* Warehouse */}
        <div className="border border-gray-200 rounded-lg p-5">
          <h3 className="font-semibold text-gray-700 mb-4">Danh sách Warehouse (Excel)</h3>
          <div className="flex gap-2">
            <input 
              type="text" 
              value={warehouseFile}
              onChange={(e) => setWarehouseFile(e.target.value)}
              placeholder="Nhập đường dẫn tuyệt đối tới file Excel..."
              className="flex-1 text-sm border border-gray-300 rounded-md px-3 py-2 focus:border-blue-500 focus:ring-blue-500"
            />
            {/* Native OS File picker simulation (Requires Electron context, but input type=file can get local path in Electron) */}
            <label className="cursor-pointer px-4 py-2 bg-gray-100 border border-gray-300 rounded-md text-sm font-medium hover:bg-gray-200 text-gray-700">
              Chọn File
              <input 
                type="file" 
                className="hidden" 
                accept=".xlsx, .xls, .csv"
                onChange={(e) => {
                  if (e.target.files && e.target.files.length > 0) {
                    const file = e.target.files[0];
                    if (window.electronAPI && typeof window.electronAPI.getPathForFile === 'function') {
                      const selectedPath = window.electronAPI.getPathForFile(file) || (file as any).path;
                      if (selectedPath) setWarehouseFile(selectedPath);
                    } else {
                      alert('Trong trình duyệt, hãy nhập đường dẫn file trên máy chủ hoặc sử dụng chức năng tải file tại màn hình Check Camera nếu phù hợp.');
                    }

                  }
                }}
              />
            </label>
          </div>
          {!window.electronAPI && (
            <p className="text-xs text-amber-600 mt-2">
              Lưu ý: Trong trình duyệt, hãy nhập đường dẫn file trên máy chủ hoặc sử dụng chức năng tải file tại màn hình Check Camera nếu phù hợp.
            </p>
          )}
        </div>

        {/* Quét Camera theo Chu kỳ */}
        <div className="border border-gray-200 rounded-lg p-5">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="font-semibold text-gray-700">Quét Camera theo Chu kỳ (Periodic Scanning)</h3>
              <p className="text-xs text-gray-500 mt-1">
                Tự động lặp lại vòng quét toàn bộ shop sau mỗi khoảng nghỉ để giám sát và phát hiện cam chập chờn.
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input 
                type="checkbox" 
                checked={periodicEnabled} 
                onChange={(e) => setPeriodicEnabled(e.target.checked)} 
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 pt-4 border-t border-gray-100">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Thời gian nghỉ giữa các chu kỳ (Phút)
              </label>
              <input 
                type="number" 
                min="1" 
                max="720"
                value={periodicInterval} 
                onChange={(e) => setPeriodicInterval(Math.max(1, parseInt(e.target.value) || 1))} 
                disabled={!periodicEnabled}
                className="w-full text-sm border border-gray-300 rounded-md px-3 py-2 focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-400"
              />
              <span className="text-[11px] text-gray-400 mt-1 block">Ví dụ: 15, 30 hoặc 60 phút</span>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Tên Sheet Google ghi nhận phục hồi
              </label>
              <input 
                type="text" 
                value={recoverySheetName} 
                onChange={(e) => setRecoverySheetName(e.target.value)} 
                placeholder="Cam chập chờn"
                disabled={!periodicEnabled}
                className="w-full text-sm border border-gray-300 rounded-md px-3 py-2 focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-400"
              />
              <span className="text-[11px] text-gray-400 mt-1 block">Tự động ghi nhận cam offline sang online vào sheet này</span>
            </div>

            <div className="col-span-1 md:col-span-2 pt-3 border-t border-gray-100 flex items-center justify-between">
              <div>
                <label className="text-xs font-medium text-gray-700 block">
                  Tự động đồng bộ dữ liệu lên Google Sheets mỗi chu kỳ
                </label>
                <span className="text-[11px] text-gray-400 block">
                  Tự động cập nhật toàn bộ 5 sheet và sheet Cam chập chờn sau mỗi vòng quét hoàn tất.
                </span>
              </div>
              <input
                type="checkbox"
                checked={periodicAutoSync}
                onChange={(e) => setPeriodicAutoSync(e.target.checked)}
                disabled={!periodicEnabled}
                className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500 disabled:opacity-50 cursor-pointer"
              />
            </div>
          </div>
        </div>

        {/* Diagnostics / Logs */}
        <div className="border border-gray-200 rounded-lg p-5">
          <h3 className="font-semibold text-gray-700 mb-4">Hệ thống Log & Gỡ lỗi (Diagnostics)</h3>
          <div className="flex gap-4 items-center">
            <button
              onClick={() => {
                if (window.electronAPI) {
                  window.electronAPI.send('open-logs');
                } else {
                  alert('Tính năng mở thư mục trực tiếp chỉ hỗ trợ trên ứng dụng Electron Desktop. File log được lưu tại runtime/logs trên máy tính server.');
                }
              }}
              className="px-4 py-2 bg-blue-100 text-blue-700 border border-blue-300 rounded-md text-sm font-medium hover:bg-blue-200"
            >
              Mở thư mục Log
            </button>
            <button
              onClick={() => {
                if (window.electronAPI) {
                  if (window.confirm('Bạn có chắc chắn muốn xóa toàn bộ file log không?')) {
                    window.electronAPI.send('clear-logs');
                    alert('Đã gửi yêu cầu xóa log.');
                  }
                } else {
                  alert('Tính năng quản lý file log trực tiếp chỉ hỗ trợ trên ứng dụng Electron Desktop.');
                }
              }}
              className="px-4 py-2 bg-red-100 text-red-700 border border-red-300 rounded-md text-sm font-medium hover:bg-red-200"
            >
              Xóa Logs
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-3">
            Hệ thống đang ghi nhận log tập trung cho UI, Electron và Backend. File log được tạo mới mỗi ngày.
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-4 mt-2">
          <button 
            onClick={handleSave}
            disabled={saving}
            className="px-6 py-2 bg-green-600 text-white font-bold rounded-md hover:bg-green-700 disabled:opacity-50"
          >
            {saving ? 'Đang lưu...' : 'Lưu & Đóng'}
          </button>
          
          {message && <span className="text-green-600 font-medium text-sm">{message}</span>}
          {error && <span className="text-red-600 font-medium text-sm">{error}</span>}
        </div>

      </div>
    </div>
  );
};

export default Settings;
