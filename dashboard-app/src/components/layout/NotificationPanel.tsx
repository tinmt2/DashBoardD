import React, { useState, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { X, RefreshCw, CheckCheck, Trash2 } from 'lucide-react';
import { useNotification } from '../../context/NotificationContext';
import { SyncNotificationItem } from '../../types/notification';
import { formatTimeAgo, formatFullDate, formatDateShort } from '../../utils/dateUtils';

const formatNumber = (num?: number | null) => {
  if (num === undefined || num === null || isNaN(num)) return '0';
  return new Intl.NumberFormat('vi-VN').format(num);
};

const formatErrorMessage = (msg?: string | null): string => {
  if (!msg) return 'Thất bại';
  const lower = msg.toLowerCase();
  if (lower.includes('invalid session') || lower.includes('session not authenticated') || lower.includes('session')) {
    return 'Phiên hết hạn';
  }
  if (lower.includes('hết hạn') || lower.includes('chưa đăng nhập') || lower.includes('401') || lower.includes('403') || lower.includes('forbidden') || lower.includes('not authenticated')) {
    return 'Hết hạn đăng nhập';
  }
  if (lower.includes('kết nối') || lower.includes('timeout') || lower.includes('network') || lower.includes('failed to fetch')) {
    return 'Lỗi kết nối';
  }
  if (msg.length > 28) {
    return msg.slice(0, 26) + '...';
  }
  return msg;
};

const getChainUnit = (chainName: string): string => {
  const lower = (chainName || '').toLowerCase();
  if (lower.includes('fpt') || lower.includes('shop')) {
    return 'calllog';
  }
  if (lower.includes('vaccine')) {
    return 'phiếu';
  }
  return 'ticket';
};

const NotificationPanel: React.FC = () => {
  const { 
    notifications, 
    unreadCount, 
    loading, 
    isPanelOpen, 
    closePanel, 
    markAsRead, 
    markAllAsRead, 
    removeNotification, 
    removeAllNotifications,
    refreshNotifications 
  } = useNotification();

  const [activeTab, setActiveTab] = useState<'all' | 'success' | 'failed' | 'unread'>('all');
  const [confirmClearOpen, setConfirmClearOpen] = useState(false);

  const filteredNotifications = useMemo(() => {
    switch (activeTab) {
      case 'success':
        return notifications.filter(n => n.status === 'SUCCESS');
      case 'failed':
        return notifications.filter(n => n.status === 'FAILED' || n.status === 'PARTIAL');
      case 'unread':
        return notifications.filter(n => !n.is_read);
      case 'all':
      default:
        return notifications;
    }
  }, [notifications, activeTab]);

  if (!isPanelOpen) return null;

  return createPortal(
    <div className="fixed inset-0 z-[9999] flex justify-end animate-fade-in">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity"
        onClick={closePanel}
      />

      {/* Flyout Drawer */}
      <div 
        className="relative w-full sm:w-[480px] bg-white h-full shadow-2xl flex flex-col z-10 border-l border-slate-200/80 animate-slide-left select-none text-slate-800"
      >
        {/* Top Header */}
        <div className="p-4 sm:px-6 border-b border-slate-200/80 bg-slate-50/70 flex items-center justify-between shrink-0">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-[16px] font-bold text-slate-900">Lịch sử đồng bộ</h2>
              {unreadCount > 0 && (
                <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-rose-500 text-white shadow-2xs">
                  {unreadCount} mới
                </span>
              )}
            </div>
            <p className="text-[12px] text-slate-500 mt-0.5">
              Thông báo số calllog và ticket mới được cập nhật vào hệ thống
            </p>
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={() => refreshNotifications()}
              disabled={loading}
              title="Làm mới"
              className="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer disabled:opacity-50"
            >
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            </button>

            {unreadCount > 0 && (
              <button
                onClick={() => markAllAsRead()}
                title="Đánh dấu tất cả đã đọc"
                className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors cursor-pointer"
              >
                <CheckCheck size={17} />
              </button>
            )}

            {notifications.length > 0 && (
              <button
                onClick={() => setConfirmClearOpen(true)}
                title="Xoá tất cả thông báo"
                className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
              >
                <Trash2 size={16} />
              </button>
            )}

            <button
              onClick={closePanel}
              title="Đóng (Esc)"
              className="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer ml-1"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="px-4 sm:px-6 py-2.5 border-b border-slate-100 flex items-center gap-1.5 shrink-0 bg-white">
          <button
            onClick={() => setActiveTab('all')}
            className={`px-3 py-1.5 rounded-xl text-[12px] font-semibold transition-all cursor-pointer ${
              activeTab === 'all'
                ? 'bg-slate-900 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            Tất cả ({notifications.length})
          </button>

          <button
            onClick={() => setActiveTab('success')}
            className={`px-3 py-1.5 rounded-xl text-[12px] font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'success'
                ? 'bg-emerald-600 text-white shadow-sm font-bold'
                : 'text-slate-600 hover:text-emerald-700 hover:bg-emerald-50'
            }`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${activeTab === 'success' ? 'bg-white' : 'bg-emerald-500'}`} />
            Thành công ({notifications.filter(n => n.status === 'SUCCESS').length})
          </button>

          <button
            onClick={() => setActiveTab('failed')}
            className={`px-3 py-1.5 rounded-xl text-[12px] font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'failed'
                ? 'bg-rose-600 text-white shadow-sm font-bold'
                : 'text-slate-600 hover:text-rose-700 hover:bg-rose-50'
            }`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${activeTab === 'failed' ? 'bg-white' : 'bg-rose-500'}`} />
            Có lỗi ({notifications.filter(n => n.status === 'FAILED' || n.status === 'PARTIAL').length})
          </button>

          <button
            onClick={() => setActiveTab('unread')}
            className={`px-3 py-1.5 rounded-xl text-[12px] font-semibold transition-all cursor-pointer ml-auto ${
              activeTab === 'unread'
                ? 'bg-indigo-600 text-white shadow-sm font-bold'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            Chưa đọc ({unreadCount})
          </button>
        </div>

        {/* Notification List Body */}
        <div className="flex-1 overflow-y-auto p-3.5 sm:p-4 space-y-2 bg-slate-50/60">
          {filteredNotifications.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-8 text-slate-400">
              <h3 className="text-[14px] font-bold text-slate-700">Chưa có thông báo nào</h3>
              <p className="text-[12px] text-slate-500 max-w-[270px] mt-1.5 leading-relaxed">
                {activeTab === 'all'
                  ? 'Khi thực hiện đồng bộ, số lượng calllog và ticket mới cập nhật sẽ hiển thị tại đây.'
                  : 'Không tìm thấy thông báo nào trong danh mục đã chọn.'}
              </p>
            </div>
          ) : (
            filteredNotifications.map(item => (
              <NotificationCard 
                key={item.id} 
                item={item} 
                onMarkRead={() => markAsRead(item.id)}
                onDelete={() => removeNotification(item.id)}
              />
            ))
          )}
        </div>

        {/* Confirmation Modal for Clearing All */}
        {confirmClearOpen && (
          <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
            <div className="bg-white rounded-2xl shadow-2xl p-5 max-w-xs w-full text-center border border-slate-200">
              <h4 className="text-[15px] font-bold text-slate-900 mb-1">Xoá toàn bộ thông báo?</h4>
              <p className="text-[12px] text-slate-500 mb-4">
                Hành động này sẽ xoá sạch tất cả lịch sử thông báo đồng bộ. Bạn không thể hoàn tác.
              </p>
              <div className="flex items-center gap-2 justify-center">
                <button
                  onClick={() => setConfirmClearOpen(false)}
                  className="px-3.5 py-1.5 text-[13px] font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
                >
                  Huỷ
                </button>
                <button
                  onClick={() => {
                    removeAllNotifications();
                    setConfirmClearOpen(false);
                  }}
                  className="px-4 py-1.5 text-[13px] font-bold text-white bg-rose-600 hover:bg-rose-700 rounded-xl transition-colors shadow-sm shadow-rose-600/30 cursor-pointer"
                >
                  Xác nhận xoá
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>,
    document.body
  );
};

interface CardProps {
  item: SyncNotificationItem;
  onMarkRead: () => void;
  onDelete: () => void;
}

/**
 * Minimalist Single-Layer Notification Item:
 * Simple, clean, no nested card boxes, no icons, instantly readable at a glance.
 */
const NotificationCard: React.FC<CardProps> = ({ item, onMarkRead, onDelete }) => {
  const isSuccess = item.status === 'SUCCESS';
  const isPartial = item.status === 'PARTIAL';
  const isFailed = item.status === 'FAILED';

  const isMultiChain = item.sync_type === 'SYNC_ALL' || item.sync_type === 'AUTO_SYNC' || (item.chain_details && item.chain_details.length > 1);
  const isExcel = item.sync_type === 'IMPORT_EXCEL';
  const isAutoSync = item.sync_type === 'AUTO_SYNC';

  const singleChainDetail = item.chain_details && item.chain_details.length === 1 ? item.chain_details[0] : null;
  const chainName = singleChainDetail?.chain || (
    item.sync_type === 'FPT_SHOP' ? 'FPT Shop' : 
    item.sync_type === 'LONG_CHAU' ? 'Long Châu' : 
    item.sync_type === 'VACCINE' ? 'Vaccine' : 'Hệ thống'
  );

  const titleText = isAutoSync ? (isMultiChain ? 'Tự động đồng bộ ngầm' : chainName) : (isMultiChain ? 'Đồng bộ tất cả 3 chuỗi' : chainName);
  const modeText = isExcel ? 'Nhập Excel' : isAutoSync ? 'Định kỳ máy chủ' : 'Tự động';
  const totalNew = item.total_new_errors || (singleChainDetail?.new_records ?? 0);
  const unitLabel = getChainUnit(chainName);

  return (
    <div
      onClick={() => {
        if (!item.is_read) onMarkRead();
      }}
      className={`group relative bg-white rounded-xl p-3 border transition-all duration-150 cursor-pointer ${
        !item.is_read
          ? 'border-indigo-200/90 bg-indigo-50/20 shadow-xs'
          : 'border-slate-200/80 hover:border-slate-300 hover:bg-slate-50/40 shadow-xs'
      }`}
    >
      {/* Row 1: Title, Metric or Status, and Close/Delete action */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 min-w-0">
          {!item.is_read && (
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 shrink-0" />
          )}
          <span className="text-[13.5px] font-bold text-slate-800 tracking-tight truncate">
            {titleText}
          </span>
          <span className="text-[11px] font-medium text-slate-400 shrink-0">
            • {modeText}
          </span>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          {isMultiChain ? (
            isSuccess ? (
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200/70">
                Thành công
              </span>
            ) : isPartial ? (
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200/70">
                Một phần
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200/70">
                Thất bại
              </span>
            )
          ) : (
            isSuccess ? (
              <span className={`text-[13px] font-bold ${
                totalNew > 0 ? 'text-emerald-700 font-extrabold' : 'text-slate-600'
              }`}>
                {totalNew > 0 ? `+${formatNumber(totalNew)}` : '0'} {unitLabel}
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200/70">
                Thất bại
              </span>
            )
          )}

          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            title="Xoá thông báo"
            className="p-1 text-slate-300 hover:text-rose-600 hover:bg-rose-50 rounded-md transition-colors cursor-pointer opacity-70 sm:opacity-0 sm:group-hover:opacity-100"
          >
            <X size={14} />
          </button>
        </div>
      </div>

      {/* Row 2: Time ago, Date range, and single-chain status/error */}
      <div className="flex items-center justify-between gap-2 mt-1 text-[11.5px] text-slate-400">
        <div className="flex items-center gap-1.5 min-w-0 flex-wrap">
          <span title={formatFullDate(item.created_at)}>
            {formatTimeAgo(item.created_at)}
          </span>
          {item.start_date && (
            <>
              <span className="text-slate-300">•</span>
              <span className="text-slate-500">
                {formatDateShort(item.start_date)}
                {item.end_date && item.end_date !== item.start_date ? ` → ${formatDateShort(item.end_date)}` : ''}
              </span>
            </>
          )}
        </div>

        {!isMultiChain && (
          <div className="shrink-0 text-right">
            {isSuccess ? (
              <span className="text-[11px] font-medium text-emerald-600">Thành công</span>
            ) : (
              <span 
                className="text-[11px] font-medium text-rose-600 truncate max-w-[180px] inline-block"
                title={item.error_message || singleChainDetail?.error_message || ''}
              >
                {formatErrorMessage(item.error_message || singleChainDetail?.error_message)}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Multi-Chain Breakdown: Clean borderless rows, no nested cards */}
      {isMultiChain && item.chain_details && item.chain_details.length > 0 && (
        <div className="mt-2 pt-2 border-t border-slate-100 space-y-1">
          {item.chain_details.map((detail, idx) => {
            const chainItemName = detail.chain;
            const unit = getChainUnit(chainItemName);
            const isOk = detail.status === 'SUCCESS';
            const newCount = detail.new_records || 0;

            return (
              <div 
                key={idx}
                className="flex items-center justify-between text-[12px] py-0.5 text-slate-600"
              >
                <span className="font-medium text-slate-700">
                  {chainItemName}
                </span>

                {isOk ? (
                  <span className={`font-bold ${
                    newCount > 0 ? 'text-emerald-700 font-extrabold' : 'text-slate-500'
                  }`}>
                    {newCount > 0 ? `+${formatNumber(newCount)} ${unit}` : `0 ${unit}`}
                  </span>
                ) : (
                  <span 
                    className="text-[11px] font-semibold text-rose-600" 
                    title={detail.error_message || 'Thất bại'}
                  >
                    {formatErrorMessage(detail.error_message)}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default NotificationPanel;
