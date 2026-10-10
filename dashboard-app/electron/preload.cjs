const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electron', {
  window: {
    minimize: () => ipcRenderer.send('window-min'),
    maximize: () => ipcRenderer.send('window-max'),
    close: () => ipcRenderer.send('window-close'),
    onStateChange: (callback) => {
      ipcRenderer.on('window-state', (_event, isMaximized) => callback(isMaximized));
    },
    removeStateChange: () => {
      ipcRenderer.removeAllListeners('window-state');
    }
  }
});

contextBridge.exposeInMainWorld('opsMonitor', {
  version: '1.0.0',
});
