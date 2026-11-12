import * as fs from 'fs';
import * as path from 'path';

// Generate session ID once at startup
function uuidv4() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}
export const SESSION_ID = uuidv4();

let cachedLogDir: string | null = null;

export function getLogDir(appDataPath: string): string {
    if (cachedLogDir) return cachedLogDir;

    const primaryDir = 'D:\\test_app_logs';
    const fallbackDir = path.join(appDataPath, 'test_app', 'runtime', 'logs');

    try {
        if (!fs.existsSync(primaryDir)) {
            fs.mkdirSync(primaryDir, { recursive: true });
        }
        // Test write permission
        const testFile = path.join(primaryDir, '.write_test');
        fs.writeFileSync(testFile, 'test');
        fs.unlinkSync(testFile);
        
        cachedLogDir = primaryDir;
        return primaryDir;
    } catch (e) {
        console.warn(`LOG_STORAGE_FALLBACK: Unable to write logs to ${primaryDir}, using fallback runtime log directory. Error: ${e}`);
        if (!fs.existsSync(fallbackDir)) {
            fs.mkdirSync(fallbackDir, { recursive: true });
        }
        cachedLogDir = fallbackDir;
        return fallbackDir;
    }
}

function getLogFilePath(appDataPath: string, layer: 'electron' | 'frontend') {
    const date = new Date().toISOString().split('T')[0];
    return path.join(getLogDir(appDataPath), `${layer}-${date}.log`);
}

function redact(obj: any): any {
    const sensitiveKeys = new Set(['password', 'token', 'access_token', 'refresh_token', 'cookie', 'authorization']);
    if (typeof obj === 'object' && obj !== null) {
        if (Array.isArray(obj)) {
            return obj.map(redact);
        }
        const newObj: any = {};
        for (const [k, v] of Object.entries(obj)) {
            if (sensitiveKeys.has(k.toLowerCase())) {
                newObj[k] = '***REDACTED***';
            } else {
                newObj[k] = redact(v);
            }
        }
        return newObj;
    }
    return obj;
}

const LOG_LEVEL_MAP: Record<string, number> = {
    'TRACE': 10,
    'DEBUG': 20,
    'INFO': 30,
    'WARN': 40,
    'ERROR': 50
};

export function writeLog(appDataPath: string, layer: 'electron' | 'frontend', level: string, event: string, message: string, opts: any = {}) {
    const minLevelStr = process.env.LOG_LEVEL ? process.env.LOG_LEVEL.toUpperCase() : 'INFO';
    const minLevel = LOG_LEVEL_MAP[minLevelStr] || 30;
    const currentLevel = LOG_LEVEL_MAP[level.toUpperCase()] || 30;
    
    if (currentLevel < minLevel) {
        return;
    }
    
    try {
        const logFilePath = getLogFilePath(appDataPath, layer);
        const logEntry = {
            timestamp: new Date().toISOString(),
            level: level.toUpperCase(),
            layer,
            event,
            message,
            session_id: SESSION_ID,
            action_id: opts.action_id || undefined,
            job_id: opts.job_id || undefined,
            module: opts.module || undefined,
            metadata: opts.metadata ? redact(opts.metadata) : undefined,
            error_type: opts.error_type || undefined,
            error_message: opts.error_message || undefined,
            stack_trace: opts.stack_trace || undefined,
        };
        fs.appendFileSync(logFilePath, JSON.stringify(logEntry) + '\n', 'utf8');
    } catch (e) {
        console.error('Failed to write log', e);
    }
}
