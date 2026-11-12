export interface IElectronAPI {
  onBackendStatus: (callback: (data: {status: string, message?: string}) => void) => void;
  getPathForFile?: (file: File) => string;
  minimize: () => void;
  maximize: () => void;
  close: () => void;
  send: (channel: string, data?: any) => void;
  invoke: (channel: string, ...args: any[]) => Promise<any>;
}

declare global {
  interface Window {
    electronAPI?: IElectronAPI;
    __API_BASE_URL__?: string;
  }
}
