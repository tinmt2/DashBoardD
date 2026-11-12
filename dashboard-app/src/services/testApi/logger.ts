// Action ID generator for request tracing
export function generateActionId(): string {
  return 'act_' + Math.random().toString(36).substring(2, 9);
}

// Global session ID fetching & caching in sessionStorage
let sessionId: string | null = null;

export async function getSessionId(): Promise<string> {
  if (sessionId) return sessionId;
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
  return sessionId;
}

export const testLogger = {
  info: (event: string, message: string, opts: any = {}) => {
    console.info(`[TEST][INFO][${event}] ${message}`, opts);
  },
  error: (event: string, message: string, opts: any = {}) => {
    console.error(`[TEST][ERROR][${event}] ${message}`, opts);
  },
  warn: (event: string, message: string, opts: any = {}) => {
    console.warn(`[TEST][WARN][${event}] ${message}`, opts);
  },
  debug: (event: string, message: string, opts: any = {}) => {
    console.debug(`[TEST][DEBUG][${event}] ${message}`, opts);
  }
};
