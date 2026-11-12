// Generate action ID
export function generateActionId() {
    return 'act_' + Math.random().toString(36).substring(2, 9);
}

// Ensure type definitions for electronAPI
declare global {
  // Uses IElectronAPI from globals.d.ts
}

export const logger = {
    info: (event: string, message: string, opts: any = {}) => {
        if (window.electronAPI) {
            window.electronAPI.send('log-from-frontend', {
                level: 'INFO',
                event,
                message,
                opts
            });
        } else {
            console.info(`[INFO][${event}] ${message}`, opts);
        }
    },
    error: (event: string, message: string, opts: any = {}) => {
        if (window.electronAPI) {
            window.electronAPI.send('log-from-frontend', {
                level: 'ERROR',
                event,
                message,
                opts
            });
        } else {
            console.error(`[ERROR][${event}] ${message}`, opts);
        }
    },
    warn: (event: string, message: string, opts: any = {}) => {
        if (window.electronAPI) {
            window.electronAPI.send('log-from-frontend', {
                level: 'WARN',
                event,
                message,
                opts
            });
        } else {
            console.warn(`[WARN][${event}] ${message}`, opts);
        }
    },
    debug: (event: string, message: string, opts: any = {}) => {
        if (window.electronAPI) {
            window.electronAPI.send('log-from-frontend', {
                level: 'DEBUG',
                event,
                message,
                opts
            });
        } else {
            console.debug(`[DEBUG][${event}] ${message}`, opts);
        }
    }
};

// Global session ID fetching
let sessionId: string | null = null;
export async function getSessionId() {
    if (sessionId) return sessionId;
    if (window.electronAPI) {
        sessionId = await window.electronAPI.invoke('get-session-id');
    } else {
        try {
            const cached = sessionStorage.getItem('test_lc_session_id');
            if (cached) {
                sessionId = cached;
            } else {
                const generated = 'sess_web_' + Date.now().toString(36) + '_' + Math.random().toString(36).substring(2, 9);
                sessionStorage.setItem('test_lc_session_id', generated);
                sessionId = generated;
            }
        } catch {
            sessionId = 'sess_web_' + Date.now().toString(36) + '_' + Math.random().toString(36).substring(2, 9);
        }
    }
    return sessionId;
}
