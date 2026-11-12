import { contextBridge, ipcRenderer, webUtils } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
  onBackendStatus: (callback: (data: {status: string, message?: string}) => void) => {
    ipcRenderer.on('backend-status', (_event, data) => callback(data));
  },
  getPathForFile: (file: File) => {
    return webUtils.getPathForFile(file);
  },
  minimize: () => ipcRenderer.send('window-minimize'),
  maximize: () => ipcRenderer.send('window-maximize'),
  close: () => ipcRenderer.send('window-close'),
  send: (channel: string, data?: any) => {
    if (['log-from-frontend', 'open-logs', 'clear-logs'].includes(channel)) {
      ipcRenderer.send(channel, data);
    }
  },
  invoke: (channel: string, ...args: any[]) => {
    if (['get-session-id', 'get-backend-status', 'restart-app', 'restart-backend'].includes(channel)) {
      return ipcRenderer.invoke(channel, ...args);
    }
  }
});
