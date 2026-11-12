export const dashboardMockData = {
  summary: {
    totalCameras: 12482,
    totalCamerasTrend: [11200, 11500, 11400, 11800, 12100, 12200, 12482],
    cameraGrowth: 1.2,
    onlineRate: 95.0,
    onlineRateTrend: [92, 93, 91, 94, 94.5, 94.8, 95.0],
    onlineGrowth: 0.4,
    errors: 162,
    errorsTrend: [210, 190, 205, 180, 175, 168, 162],
    errorsGrowth: -5.2,
    activeJobs: 2,
  },

  errorTrend: [
    { label: 'Thứ 2', new: 82, resolved: 61 },
    { label: 'Thứ 3', new: 96, resolved: 72 },
    { label: 'Thứ 4', new: 71, resolved: 80 },
    { label: 'Thứ 5', new: 114, resolved: 76 },
    { label: 'Thứ 6', new: 88, resolved: 92 },
    { label: 'Thứ 7', new: 126, resolved: 84 },
    { label: 'Hôm nay', new: 104, resolved: 91 },
  ],

  cameraStatus: [
    { label: 'Online', count: 11856, color: '#10b981', unit: 'Camera' },
    { label: 'Offline', count: 426, color: '#f59e0b', unit: 'Camera' },
    { label: 'Lỗi', count: 162, color: '#f87171', unit: 'Camera' },
    { label: 'Khác', count: 38, color: '#64748b', unit: 'Camera' }
  ],
  
  jobStatus: [
    { label: 'Đang chạy', count: 2, color: '#10b981', unit: 'tác vụ' },
    { label: 'Đang chờ', count: 1, color: '#3b82f6', unit: 'tác vụ' },
    { label: 'Hoàn thành', count: 8, color: '#475569', unit: 'tác vụ' },
    { label: 'Lỗi', count: 1, color: '#f87171', unit: 'tác vụ' }
  ],

  regions: [
    { name: 'North', shops: 1240, offline: 156, trend: [140, 145, 150, 148, 152, 155, 156], status: 'Warning', statusColor: 'amber' },
    { name: 'Central', shops: 850, offline: 42, trend: [60, 55, 50, 48, 45, 43, 42], status: 'Healthy', statusColor: 'emerald' },
    { name: 'South', shops: 1284, offline: 228, trend: [190, 200, 215, 210, 220, 225, 228], status: 'Critical', statusColor: 'red' }
  ],

  dvr: {
    total: 3210,
    errors: 47,
    statusBreakdown: {
      online: 3102,
      warning: 61,
      error: 47
    }
  },

  tasks: [
    { id: '#884', name: 'Kiểm tra Camera', progress: 82, color: '#10b981' },
    { id: '#112', name: 'Kiểm tra DVR', progress: 45, color: '#10b981' }
  ]
};
