import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { cameraApi } from '../api/camera';
import { ftelDvrApi } from '../api/ftelDvr';
import { ticketApi } from '../api/ticket';
import { motionApi } from '../api/motion';
import { logger } from '../utils/logger';

export type ModuleName = 'camera' | 'dvr' | 'ticket' | 'check-ticket' | 'motion' | 'cam_lc' | 'dvr_lc' | 'cam_vx' | 'dvr_vx' | 'ftel_lc' | 'ftel_vx';

export type JobStatus = 'idle' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface TaskState {
  jobId: string;
  module: ModuleName;
  status: JobStatus;
  progress: number;
  total: number;
  results: any[];
  error: string | null;
  [key: string]: any;
}

interface TaskContextValue {
  tasks: Record<string, TaskState>;
  startTask: (module: ModuleName, jobId: string, initialState?: any) => void;
  clearTask: (module: ModuleName) => void;
}

const TaskContext = createContext<TaskContextValue | undefined>(undefined);

export const TaskProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [tasks, setTasks] = useState<Record<string, TaskState>>({});
  const intervalsRef = useRef<Record<string, ReturnType<typeof setInterval>>>({});
  const previousStatusRef = useRef<Record<string, JobStatus>>({});

  const startTask = (module: ModuleName, jobId: string, initialState: any = {}) => {
    logger.info(`TASK_CREATED`, `Task created for module ${module}`, { job_id: jobId, module });
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
            logger.info(event, `Task status changed to ${status}`, { job_id: jobId, module, metadata: { status } });
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
          logger.error('TASK_FAILED', `Task failed to fetch status`, { job_id: jobId, module, error_message: res.message });
          setTasks((prev) => ({
            ...prev,
            [module]: {
              ...prev[module],
              status: 'failed',
              error: res.message || 'Lỗi khi lấy trạng thái',
            },
          }));
        }
      } catch (err) {
        // network error, keep trying
      }
    }, 1000);
  };

  const clearTask = (module: ModuleName) => {
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
    <TaskContext.Provider value={{ tasks, startTask, clearTask }}>
      {children}
    </TaskContext.Provider>
  );
};

export const useTaskContext = () => {
  const context = useContext(TaskContext);
  if (!context) throw new Error('useTaskContext must be used within TaskProvider');
  return context;
};

