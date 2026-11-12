import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { cameraApi } from '../services/testApi/cameraApi';
import { ftelDvrApi } from '../services/testApi/ftelDvrApi';
import { ticketApi } from '../services/testApi/ticketApi';
import { motionApi } from '../services/testApi/motionApi';
import { testLogger } from '../services/testApi/logger';

export type TestModuleName =
  | 'camera'
  | 'dvr'
  | 'ticket'
  | 'check-ticket'
  | 'motion'
  | 'cam_lc'
  | 'dvr_lc'
  | 'cam_vx'
  | 'dvr_vx'
  | 'ftel_lc'
  | 'ftel_vx';

export type TestJobStatus = 'idle' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface TestTaskState {
  jobId: string;
  module: TestModuleName;
  status: TestJobStatus;
  progress: number;
  total: number;
  results: any[];
  error: string | null;
  [key: string]: any;
}

interface TestTaskContextValue {
  tasks: Record<string, TestTaskState>;
  startTask: (module: TestModuleName, jobId: string, initialState?: any) => void;
  clearTask: (module: TestModuleName) => void;
}

const TestTaskContext = createContext<TestTaskContextValue | undefined>(undefined);

export const TestTaskProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [tasks, setTasks] = useState<Record<string, TestTaskState>>({});
  const intervalsRef = useRef<Record<string, ReturnType<typeof setInterval>>>({});
  const previousStatusRef = useRef<Record<string, TestJobStatus>>({});

  const startTask = (module: TestModuleName, jobId: string, initialState: any = {}) => {
    testLogger.info('TASK_CREATED', `Task created for module ${module}`, { job_id: jobId, module });
    previousStatusRef.current[module] = 'queued';
    setTasks((prev) => ({
      ...prev,
      [module]: {
        jobId,
        module,
        status: 'queued',
        progress: 0,
        total: 0,
        results: [],
        error: null,
        ...initialState,
      },
    }));

    if (intervalsRef.current[module]) {
      clearInterval(intervalsRef.current[module]);
    }

    intervalsRef.current[module] = setInterval(async () => {
      let res: any;
      try {
        switch (module) {
          case 'camera':
          case 'cam_lc':
          case 'cam_vx':
          case 'dvr_lc':
          case 'dvr_vx':
            res = await cameraApi.getJob(jobId);
            break;
          case 'ftel_lc':
          case 'ftel_vx':
            res = await ftelDvrApi.getJob(jobId);
            break;
          case 'dvr':
            res = await ftelDvrApi.getStatus();
            break;
          case 'ticket':
          case 'check-ticket':
            res = await ticketApi.getJob(jobId);
            break;
          case 'motion':
            res = await motionApi.getJob(jobId);
            break;
        }

        if (res && res.success && res.data) {
          const status = res.data.status;
          if (previousStatusRef.current[module] !== status) {
            previousStatusRef.current[module] = status;
            const event = `TASK_${status.toUpperCase()}`;
            testLogger.info(event, `Task status changed to ${status}`, { job_id: jobId, module, metadata: { status } });
          }

          setTasks((prev) => ({
            ...prev,
            [module]: { ...prev[module], ...res.data, jobId },
          }));

          if (status === 'completed' || status === 'failed' || status === 'cancelled' || status === 'idle') {
            clearInterval(intervalsRef.current[module]);
            delete intervalsRef.current[module];
          }
        } else if (res && !res.success) {
          clearInterval(intervalsRef.current[module]);
          delete intervalsRef.current[module];
          testLogger.error('TASK_FAILED', 'Task failed to fetch status', { job_id: jobId, module, error_message: res.message });
          setTasks((prev) => ({
            ...prev,
            [module]: {
              ...prev[module],
              status: 'failed',
              error: res.message || 'Lỗi khi lấy trạng thái',
            },
          }));
        }
      } catch {
        // network error, keep polling
      }
    }, 1000);
  };

  const clearTask = (module: TestModuleName) => {
    setTasks((prev) => {
      const newTasks = { ...prev };
      const task = newTasks[module];
      if (task && (task.status === 'completed' || task.status === 'failed' || task.status === 'cancelled' || task.status === 'idle')) {
        delete newTasks[module];
      }
      return newTasks;
    });
  };

  useEffect(() => {
    return () => {
      Object.values(intervalsRef.current).forEach(clearInterval);
    };
  }, []);

  return (
    <TestTaskContext.Provider value={{ tasks, startTask, clearTask }}>
      {children}
    </TestTaskContext.Provider>
  );
};

export const useTestTaskContext = () => {
  const context = useContext(TestTaskContext);
  if (!context) throw new Error('useTestTaskContext must be used within TestTaskProvider');
  return context;
};
