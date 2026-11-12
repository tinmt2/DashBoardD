import { app, BrowserWindow, ipcMain } from 'electron';
import * as path from 'path';
import { fileURLToPath } from 'url';
import { spawn, ChildProcess, exec } from 'child_process';
import * as http from 'http';
import * as net from 'net';
import { writeLog, SESSION_ID, getLogDir } from './logger.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

let mainWindow: BrowserWindow | null = null;
let pythonProcess: ChildProcess | null = null;
let currentMessage: string | undefined;
let backendStatus: 'Starting' | 'Ready' | 'Error' | 'Stopped' | 'PortConflict' | 'Timeout' = 'Stopped';
let isShuttingDown = false;

const PORT = 18020;

// Single instance lock
if (isDev) {
  // Use a separate user data path for dev to avoid cache locks
  app.setPath('userData', path.join(app.getPath('appData'), 'test_app_dev'));
}
const gotTheLock = app.requestSingleInstanceLock();

writeLog(app.getPath('appData'), 'electron', 'INFO', 'ELECTRON_START', 'Electron Main Process Starting');
if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });
}

function updateStatus(status: typeof backendStatus, message?: string) {
  currentMessage = message;
  const isChanged = backendStatus !== status;
  backendStatus = status;
  
  if (isChanged) {
    const eventName = status === 'PortConflict' ? 'PORT_CONFLICT' : `BACKEND_${status.toUpperCase()}`;
    console.log(`[Electron] Backend status changed: ${status}${message ? ` - ${message}` : ''}`);
    writeLog(app.getPath('appData'), 'electron', 'INFO', eventName, `Backend status: ${status}`, { metadata: { status, message } });
  }
  
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send('backend-status', { status, message });
  }
}

function checkPortInUse(port: number, callback: (inUse: boolean) => void) {
  const server = net.createServer();
  server.once('error', (err: any) => {
    if (err.code === 'EADDRINUSE') {
      callback(true);
    } else {
      callback(false);
    }
  });
  server.once('listening', () => {
    server.close();
    callback(false);
  });
  server.listen(port, '127.0.0.1');
}


let isStarting = false;

async function attemptSelfHealing(): Promise<boolean> {
  writeLog(app.getPath('appData'), 'electron', 'INFO', 'BACKEND_PORT_OCCUPIED', `Port ${PORT} is occupied, attempting self-healing`);
  
  // 1. Health Validation
  writeLog(app.getPath('appData'), 'electron', 'INFO', 'BACKEND_HEALTH_CHECK', `Checking if occupant is our backend`);
  const isOurBackend = await new Promise<boolean>((resolve) => {
    const req = http.get(`http://127.0.0.1:${PORT}/health`, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          if (res.statusCode === 200 && json.status === 'ok' && json.service === 'test-python-backend') {
            resolve(true);
          } else {
            resolve(false);
          }
        } catch (e) {
          resolve(false);
        }
      });
    });
    req.on('error', () => resolve(false));
    req.setTimeout(2000, () => { req.destroy(); resolve(false); });
  });

  if (!isOurBackend) {
    writeLog(app.getPath('appData'), 'electron', 'WARN', 'BACKEND_SELF_HEAL_FAILED', `Occupant is not our backend or unresponsive`);
    return false;
  }
  
  writeLog(app.getPath('appData'), 'electron', 'INFO', 'BACKEND_ORPHAN_DETECTED', `Orphan backend detected on port ${PORT}`);

  // 2. PID Identification
  const pid = await new Promise<number | null>((resolve) => {
    exec(`netstat -ano | findstr LISTENING | findstr :${PORT}`, (err, stdout) => {
      if (err || !stdout) return resolve(null);
      const lines = stdout.trim().split('\n');
      for (const line of lines) {
        if (line.includes(`:${PORT}`) && line.includes('LISTENING')) {
          const parts = line.trim().split(/\s+/);
          const p = parseInt(parts[parts.length - 1], 10);
          if (!isNaN(p) && p > 0) return resolve(p);
        }
      }
      resolve(null);
    });
  });

  if (!pid) {
    writeLog(app.getPath('appData'), 'electron', 'ERROR', 'BACKEND_SELF_HEAL_FAILED', `Could not identify PID for port ${PORT}`);
    return false;
  }
  
  writeLog(app.getPath('appData'), 'electron', 'INFO', 'BACKEND_PID_IDENTIFIED', `Identified PID ${pid}`);

  // 3. PID Verification
  if (pid === process.pid) {
    writeLog(app.getPath('appData'), 'electron', 'ERROR', 'BACKEND_SELF_HEAL_FAILED', `Identified PID is our own process!`);
    return false;
  }

  const isValidProcess = await new Promise<boolean>((resolve) => {
    exec(`tasklist /fi "PID eq ${pid}" /fo csv /nh`, (err, stdout) => {
      if (err || !stdout) return resolve(false);
      const lowerOut = stdout.toLowerCase();
      if (lowerOut.includes('python.exe') || lowerOut.includes('backend.exe')) {
        if (!lowerOut.includes('electron.exe') && !lowerOut.includes('node.exe')) {
            return resolve(true);
        }
      }
      resolve(false);
    });
  });

  if (!isValidProcess) {
    writeLog(app.getPath('appData'), 'electron', 'WARN', 'BACKEND_SELF_HEAL_FAILED', `PID ${pid} failed verification (not python.exe or backend.exe)`);
    return false;
  }

  writeLog(app.getPath('appData'), 'electron', 'INFO', 'BACKEND_PID_VERIFIED', `PID ${pid} verified as orphan backend`);

  // 4. Kill Strategy
  try {
    process.kill(pid, 'SIGKILL');
    writeLog(app.getPath('appData'), 'electron', 'INFO', 'BACKEND_ORPHAN_KILLED', `Killed orphan PID ${pid}`);
  } catch (e: any) {
    writeLog(app.getPath('appData'), 'electron', 'ERROR', 'BACKEND_SELF_HEAL_FAILED', `Failed to kill PID ${pid}: ${e.message}`);
    return false;
  }

  // 5. Port Release polling
  const isReleased = await new Promise<boolean>((resolve) => {
    let attempts = 0;
    const maxAttempts = 10; // 5 seconds (500ms * 10)
    
    const check = () => {
      attempts++;
      checkPortInUse(PORT, (inUse) => {
        if (!inUse) {
          resolve(true);
        } else if (attempts >= maxAttempts) {
          resolve(false);
        } else {
          setTimeout(check, 500);
        }
      });
    };
    setTimeout(check, 500); // initial wait
  });

  if (isReleased) {
    writeLog(app.getPath('appData'), 'electron', 'INFO', 'BACKEND_PORT_RELEASED', `Port ${PORT} successfully released`);
    writeLog(app.getPath('appData'), 'electron', 'INFO', 'BACKEND_SELF_HEAL_SUCCESS', `Self-healing completed`);
    return true;
  } else {
    writeLog(app.getPath('appData'), 'electron', 'ERROR', 'BACKEND_SELF_HEAL_FAILED', `Port ${PORT} still in use after kill`);
    return false;
  }
}

async function startPythonBackend() {
  if (isStarting) return;
  isStarting = true;
  updateStatus('Starting', 'Checking port...');
  
  checkPortInUse(PORT, async (inUse) => {
    if (inUse) {
      const healed = await attemptSelfHealing();
      if (!healed) {
        updateStatus('PortConflict', `Backend port ${PORT} is already in use.`);
        isStarting = false;
        return;
      }
    }

    updateStatus('Starting', 'Starting Python process...');
    
    // Determine paths based on dev vs prod
    const projectRoot = isDev ? path.join(__dirname, '..', '..') : path.join(process.resourcesPath, 'app');
    
    if (isDev) {
      const pythonExe = path.join(projectRoot, '.venv', 'Scripts', 'python.exe');
      console.log(`[Electron] Starting Python backend (DEV) from: ${pythonExe}`);
      pythonProcess = spawn(pythonExe, ['-m', 'uvicorn', 'app.api.main:app', '--host', '127.0.0.1', '--port', String(PORT), '--no-access-log'], {
        cwd: projectRoot,
        detached: false,
          windowsHide: true,
      });
    } else {
      const backendExe = path.join(process.resourcesPath, 'backend', 'backend.exe');
      console.log(`[Electron] Starting Python backend (PROD) from: ${backendExe}`);
      pythonProcess = spawn(backendExe, [], {
        cwd: path.join(process.resourcesPath, 'backend'),
        detached: false,
          windowsHide: true,
      });
    }

    if (pythonProcess.pid) {
      console.log(`[Python] PID=${pythonProcess.pid}`);
      // Workaround for scope issue without breaking too much
      const execPath = isDev ? "python.exe" : "backend.exe";
      writeLog(app.getPath('appData'), 'electron', 'INFO', 'BACKEND_STARTED', 'Python backend process spawned', {
          metadata: { pid: pythonProcess.pid, executable: execPath }
      });
    }

    pythonProcess.stdout?.on('data', (data) => {
      console.log(`[Python STDOUT] ${data.toString().trim()}`);
    });

    pythonProcess.stderr?.on('data', (data) => {
      console.log(`[Python STDERR] ${data.toString().trim()}`);
    });

    pythonProcess.on('error', (err) => {
      console.error(`[Python ERROR] Failed to start subprocess: ${err.message}`);
      if (!isShuttingDown) updateStatus('Error', `Process error: ${err.message}`);
      isStarting = false;
    });

    pythonProcess.on('exit', (code, signal) => {
      console.log(`[Python] Process exited with code=${code} signal=${signal}`);
      writeLog(app.getPath('appData'), 'electron', code === 0 ? 'INFO' : 'ERROR', 'BACKEND_EXIT', `Python backend exited with code ${code}`, {
          error_message: signal ? `Signal: ${signal}` : undefined,
          metadata: { exit_code: code, signal }
      });
      pythonProcess = null;
      if (!isShuttingDown) {
        updateStatus('Error', `Python process exited unexpectedly (code: ${code})`);
      } else {
        updateStatus('Stopped');
      }
      isStarting = false;
    });

    pollHealthEndpoint();
  });
}
function pollHealthEndpoint() {
  const maxRetries = 30; // 30 seconds
  let retries = 0;

  const interval = setInterval(() => {
    if (backendStatus === 'Error' || backendStatus === 'Stopped' || backendStatus === 'PortConflict') {
      clearInterval(interval);
      return;
    }

    retries++;
    console.log(`[Electron] Polling /health (Attempt ${retries}/${maxRetries})...`);

    const req = http.get(`http://127.0.0.1:${PORT}/health`, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        if (res.statusCode === 200) {
          try {
            const json = JSON.parse(data);
            if (json.status === 'ok') {
              console.log('[Electron] FastAPI ready');
              clearInterval(interval);
              updateStatus('Ready');
            }
          } catch (e) {
            // parse error
          }
        }
      });
    });

    req.on('error', (err) => {
      // connection refused, still starting
    });

    req.end();

    if (retries >= maxRetries && backendStatus !== 'Ready') {
      clearInterval(interval);
      console.error('[Electron] Startup timeout reached.');
      updateStatus('Timeout', 'Backend startup timeout after 30 seconds.');
      stopPythonBackend();
    }
  }, 1000);
}

function stopPythonBackend() {
  if (pythonProcess) {
    console.log('[Electron] Shutting down Python backend');
    try {
      pythonProcess.kill('SIGTERM');
      // If it doesn't die after a few seconds, force kill
      setTimeout(() => {
        if (pythonProcess) {
          console.log('[Electron] Force killing Python backend');
          pythonProcess.kill('SIGKILL');
        }
      }, 5000);
    } catch (e) {
      console.error('[Electron] Error killing Python process:', e);
    }
  }
}


async function restartPythonBackend() {
  console.log('[Electron] Restarting Python backend...');
  isShuttingDown = false;
  updateStatus('Starting', 'Đang khởi động lại Python Backend...');
  stopPythonBackend();
  await new Promise((r) => setTimeout(r, 1000));
  await attemptSelfHealing();
  isStarting = false;
  await startPythonBackend();
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    frame: false,
    titleBarStyle: 'hidden',
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.removeMenu();

  if (isDev) {
    const devUrl = process.env.ELECTRON_DEV_URL || 'http://localhost:5175';
    mainWindow.loadURL(devUrl);
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }
  
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    // Prevent ANY new window from opening
    return { action: 'deny' };
  });

  mainWindow.webContents.on('will-navigate', (e, url) => {
    // If you want to prevent navigation away from the app
    // e.preventDefault();
  });

  mainWindow.webContents.on('did-finish-load', () => {
    updateStatus(backendStatus, backendStatus === 'PortConflict' ? `Backend port ${PORT} is already in use.` : undefined);
    if (isDev) {
      mainWindow?.webContents.openDevTools({ mode: 'right' });
    }
  });
}

if (gotTheLock) {
  // Prevent network service crashes in dev due to rapid reloads
  if (isDev) {
    app.commandLine.appendSwitch('disable-http-cache');
  }

  app.whenReady().then(() => {
    createWindow();
    startPythonBackend();

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
      }
    });
  });

  app.on('before-quit', () => {
    isShuttingDown = true;
    stopPythonBackend();
  });

  
  ipcMain.handle('restart-app', async () => {
    try {
      await restartPythonBackend();
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.reload();
      }
      return { success: true };
    } catch (err: any) {
      console.error('Failed to restart app:', err);
      return { success: false, error: err.message };
    }
  });

  ipcMain.handle('restart-backend', async () => {
    try {
      await restartPythonBackend();
      return { success: true };
    } catch (err: any) {
      console.error('Failed to restart backend:', err);
      return { success: false, error: err.message };
    }
  });

  ipcMain.handle('get-session-id', () => SESSION_ID);
  ipcMain.handle('get-backend-status', () => ({ status: backendStatus, message: currentMessage }));
  
  ipcMain.on('open-logs', () => {
    const { shell } = require('electron');
    const path = require('path');
    const fs = require('fs');
    const logDir = getLogDir(app.getPath('appData'));
    if (fs.existsSync(logDir)) {
      shell.openPath(logDir);
    }
  });

  ipcMain.on('clear-logs', () => {
    const path = require('path');
    const fs = require('fs');
    const logDir = getLogDir(app.getPath('appData'));
    if (fs.existsSync(logDir)) {
      const files = fs.readdirSync(logDir);
      for (const file of files) {
        try {
          fs.unlinkSync(path.join(logDir, file));
        } catch (e) {
          console.error("Could not delete", file, e);
        }
      }
    }
  });

  
  ipcMain.on('log-from-frontend', (event, logData) => {
    writeLog(app.getPath('appData'), 'frontend', logData.level, logData.event, logData.message, logData.opts);
  });
  
  ipcMain.on('window-minimize', () => {
    BrowserWindow.getFocusedWindow()?.minimize()
  })
  
  ipcMain.on('window-maximize', () => {
    const win = BrowserWindow.getFocusedWindow()
    if (win?.isMaximized()) {
      win.unmaximize()
    } else {
      win?.maximize()
    }
  })
  
  ipcMain.on('window-close', () => {
    BrowserWindow.getFocusedWindow()?.close()
  })

  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
      app.quit();
    }
  });
}
