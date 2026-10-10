# Multi-App Port Configuration

This document outlines the port configuration to allow multiple Electron + React + Vite applications to run simultaneously on the same machine without conflicting.

## App A (OpsMonitor)
- **Name:** opsmonitor
- **Location:** `d:/Tín/ABC/DashBoardD/dashboard-app`
- **Vite Port:** `5174` (Strict mode: enabled)
- **Backend Port:** N/A (Uses mock data or shared backend)
- **Electron Dev URL:** `http://localhost:5174`
- **Start Command:** `npm run electron:dev`

## App B (Migration Test App)
- **Name:** desktop
- **Location:** `d:/Tín/ABC/test/desktop`
- **Vite Port:** `5175` (Strict mode: enabled)
- **Backend Port:** `18020` (Python FastAPI backend)
- **Electron Dev URL:** `http://localhost:5175`
- **Start Command:** `npm run electron:dev`

## Technical Implementation Details
1. **Vite Configuration:**
   - Both apps use `strictPort: true` in their `vite.config.ts` (or `package.json` scripts) to ensure Vite fails immediately if the port is occupied, rather than silently falling back to the next available port.
2. **NPM Scripts:**
   - App A uses `vite --port 5174 --strictPort`.
   - App B uses `vite --port 5175 --strictPort`.
   - The Electron start commands pass `ELECTRON_DEV_URL` as an environment variable to guarantee the Electron main process loads the exact port Vite is serving on.
3. **Electron Main Process:**
   - Both apps check `process.env.ELECTRON_DEV_URL` before falling back to their respective defaults (`http://localhost:5174` and `http://localhost:5175`).
4. **App Data / Singleton Lock:**
   - Electron uses the `name` field in `package.json` to determine the user data directory. Since App A is named `opsmonitor` and App B is named `desktop`, they use separate user data directories. This prevents singleton lock file conflicts (`0x20` errors) when both are running simultaneously in dev mode.

## Production / Build Behavior
- In production, Electron loads the statically built files from `dist/index.html`.
- Port bindings (5174, 5175) are strictly for the Vite development server.
- The Python backend (if bundled) will run on its designated port (e.g., 18020) and is not affected by the frontend Vite port configuration.
