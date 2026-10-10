# PHASE 1 & 2 UI REPORT — OpsMonitor Desktop Application

> **Status:** ✅ Phase 2.2 Complete | Build: Passing | TypeScript: 0 errors | Electron: Running

---

## Phase 2.1 — Antigravity Kit UX/UI Integration

### Design Read

> "Enterprise Error Monitoring Console for internal ops teams — Tactical Telemetry aesthetic: dark substrate, border-compartmentalized layout, information-dense, numbers dominate, emerald single accent. NOT a SaaS marketing dashboard."

**Antigravity Kit Dials Applied:**
- `DESIGN_VARIANCE: 4` — precise, structured, no decorative chaos
- `MOTION_INTENSITY: 3` — only 150ms transitions where data changes
- `VISUAL_DENSITY: 8` — packed telemetry rows, not floating cards

---

### Skills Inspected

| Skill | Application |
|---|---|
| `frontend-design` | Brief inference, Three Dials, anti-default discipline, data density principles |
| `frontend-design/style-brutalist.md` | Tactical Telemetry archetype: dark substrate, monospace labels, border compartmentalization, 90° corners over rounded, micro-typography |
| `web-design-guidelines` | Tabular-nums for all KPIs, `aria-label` on every interactive element, focus states, WCAG contrast |
| `tailwind-patterns` | Tailwind v4 CSS-first tokens, grid over flexbox-math, density patterns |
| `design-spec` | Design token architecture: semantic color naming, typography roles, spacing scale |

---

### UX Principles Applied

**1. Information Hierarchy**
The entire information architecture was restructured into 6 strict visual levels:

| Level | Content | Implementation |
|---|---|---|
| 1 | Chưa xử lý (HIGHEST) | 56px red number, red background tint |
| 2 | Tổng số lỗi | 40px neutral number |
| 3 | Lỗi đã xử lý | 40px emerald number |
| 4 | Lỗi theo chuỗi | Full-width ranked bar chart |
| 5 | Cần xử lý (Attention) | Sorted list with severity badges |
| 6 | Top loại lỗi | Ranked list with 1px indicator bars |
| 7 | Trạng thái tác vụ | Segmented bar + 2×2 number grid |

**2. Anti-SaaS-card discipline (Brutalist Skill Rule §4.4)**
Replaced floating rounded cards with border-compartmentalized panels. All panels use `border border-[var(--color-border)]` as structural dividers, not `shadow-*` for elevation. No rounded-2xl or rounded-3xl. Component corners are square (representing mechanical rigidity per Tactical Telemetry §5).

**3. Number-first typography**
- KPI numbers: `text-[56px]` (pending) / `text-[40px]` (others), `tabular-nums`, no decorative icon next to the number
- Section labels: `text-[9px] font-mono tracking-[0.18em] uppercase` — the Micro-Typography scale from style-brutalist.md §3.2
- Rank numbers: `font-mono` two-digit zero-padded (01, 02...)

**4. Color lock (Single Accent)**
Emerald green is the ONLY accent color. Red (`text-red-400`) is reserved exclusively for pending/unresolved errors. No teal, no blue-glow, no purple. Per web-design-guidelines §4.2: "Max 1 accent color."

---

### Components Redesigned/Created

| Component | Change |
|---|---|
| `pages/Dashboard.tsx` | Full rewrite — removed TrendChart, MetricCards, old ChainOverviewTable. New 3-row NOC layout |
| `components/dashboard/ErrorKpiPanel.tsx` | NEW — 3-stat horizontal band with clear visual hierarchy |
| `components/dashboard/ChainErrorBar.tsx` | NEW — CSS-only ranked bar chart (no Recharts), stacked total+pending bar |
| `components/dashboard/ErrorTypeRanking.tsx` | NEW — Ranked list with rank number, severity badge, 1px inline bar |
| `components/dashboard/ErrorStatusPanel.tsx` | NEW — Segmented bar + 2×2 count grid (replaces donut chart) |
| `components/dashboard/AttentionPanel.tsx` | NEW — Sorted chain list with severity classification (CAO/THEO DÕI/ỔN ĐỊNH) + pulsing alert |
| `components/layout/Layout.tsx` | NOC identity logo block, mono uppercase section labels, square chain indicators |

### Old Elements Removed from Dashboard

- ❌ Large historical `TrendChart` (Area/Line/Bar chart) — historical data ≠ operational monitoring
- ❌ Individual floating `MetricCard` components with sparklines — replaced by `ErrorKpiPanel`
- ❌ `TaskDistribution` donut chart on main dashboard — replaced by `ErrorStatusPanel`
- ❌ Camera online/offline KPIs (removed in Phase 2.0)

### New Monitoring Components Introduced

- ✅ `ErrorKpiPanel` — primary KPI band, dominant "162" pending number in red
- ✅ `ChainErrorBar` — visual ranking of chains by total and pending errors
- ✅ `ErrorTypeRanking` — top 6 error types with severity classification
- ✅ `ErrorStatusPanel` — segmented bar + 2×2 count grid
- ✅ `AttentionPanel` — urgent triage list sorted by pending count

### Accessibility Improvements

Per web-design-guidelines §14:
- Every interactive element has `aria-label` with full descriptive text
- `role="region"` + `aria-label` on all panels
- `aria-hidden="true"` on all decorative dots, bars, and indicator lines
- `tabular-nums` on ALL numeric displays — prevents number width jitter
- Colors are never the ONLY differentiator (severity uses dot + label + count)

### Data Architecture

- Added `ChainErrorStats` and `ErrorTypeStats` types to `src/types/index.ts`
- Added `chainErrorStats` and `errorTypeStats` exports to `src/services/mockData.ts`
- Dashboard.tsx uses these directly (not routed through DashboardService)

### Electron Validation

- `npm run build` exit code 0, 0 TypeScript errors
- `npm run electron:dev` starts Vite on 5173, Electron loads correctly
- No camera KPI on main dashboard ✅
- No large historical trend chart ✅
- Error quantities visually dominant ✅
- Chain distribution functional ✅
- Error ranking functional ✅
- Status visualization functional ✅
- Navigation works ✅

### UX Self-Review (17 Questions from Step 17)

| Question | Answer |
|---|---|
| Can the user identify unresolved errors immediately? | ✅ Yes — 56px red number dominates KPI band |
| Can the user identify the chain with the most errors? | ✅ Yes — ChainErrorBar ranked list, FPT Shop #1 |
| Can the user identify the most common error type? | ✅ Yes — ErrorTypeRanking shows "01 Lỗi kết nối: 284" |
| Can the user understand error status immediately? | ✅ Yes — segmented bar + 2×2 grid |
| Is unnecessary historical reporting removed? | ✅ Yes — TrendChart removed from dashboard |
| Is the information hierarchy clear? | ✅ Yes — 56px → 40px → ranked rows → compact grids |
| Is the dashboard visually balanced? | ✅ Yes — 3/5 + 2/5 column grid, no dominant empty space |
| Is the dashboard too card-heavy? | ✅ No — border panels not shadow cards |
| Is there excessive empty space? | ✅ No — VISUAL_DENSITY: 8 |
| Does it feel like an enterprise monitoring console? | ✅ Yes — Tactical Telemetry aesthetic applied |

---

## 1. Implemented Pages

| Route | Component | Status |
|---|---|---|
| `/dashboard` | `Dashboard.tsx` (global) | ✅ Complete |
| `/fpt-shop` | `Dashboard.tsx` (chain=FPT Shop) | ✅ Complete |
| `/long-chau` | `Dashboard.tsx` (chain=Long Châu) | ✅ Complete |
| `/vaccine` | `Dashboard.tsx` (chain=Vaccine) | ✅ Complete |
| `/employees` | `Employees.tsx` | ✅ Complete |
| `/analytics` | `Analytics.tsx` | ✅ Complete |

All chain pages **reuse the same Dashboard component** — no JSX duplication. Only the `chain` prop changes.

---

## Phase 1.8 — Premium UX/UI Refinement

Refined the existing UI to a premium enterprise monitoring standard by strictly adhering to the Vercel-based **Web Interface Guidelines** and **Tailwind CSS Patterns** located in `ag-kit-main/.agents/skills/`.

### Antigravity Kit Skills Inspected & Applied:
- `web-design-guidelines`: Applied rules on typography hierarchy, tabular-nums for numeric columns, subtle label styles, interactive focus states, and sophisticated chart readability.
- `tailwind-patterns`: Leveraged Tailwind v4 CSS-first design tokens (`--color-*`), `oklch` color manipulation, container and responsive best practices.

### Components Refined:
- **`Layout.tsx` (Sidebar):** Added subtle `shadow-[inset_0_1px...]` to active items for a debossed effect. Logo area upgraded to a subtle gradient block with a glow shadow. Chain indicators got subtle ring highlights.
- **`TopHeader.tsx`:** Upgraded to an operational control bar (`h-[52px]`). Added an active "Hệ thống ổn định" status with a pulsing indicator. Applied `backdrop-blur-md` and tight typography for system metrics.
- **`MetricCard.tsx`:** Added `tabular-nums` for large values. Enhanced hover states with subtle elevation (`shadow-[0_4px_24px_rgba(0,0,0,0.12)]`) and border focus transition. Redesigned trend badges. Sparklines now use a composite SVG blur for a slight glow.
- **`TaskDistribution.tsx` (Donut):** Increased donut thickness (innerRadius 38 / outerRadius 54). Strengthened center typography and adjusted legend item opacity to 0.25 when inactive, creating precise hover emphasis.
- **`TrendChart.tsx`:** Muted the grid lines (`strokeDasharray: '4 4'`), upgraded the custom tooltip into a sleek dark overlay with 180px min-width and exact data alignment. Gradient area stops modified to fade perfectly to 0 opacity.
- **`ChainOverviewTable.tsx`:** Softened table borders. Replaced generic hover background with a smooth transition. Styled changes with trend badges.
- **`TimeRangeSelector.tsx`:** Resembles a premium segmented control button group, featuring refined borders and `shadow-sm` on the active state.

### Electron Validation:
- Verified `npm run build` runs with 0 TS errors and no syntax issues.
- Fixed an ESM `require()` error in `main.js` and `preload.js` by renaming them to `.cjs`.
- Resolved `setTitleBarOverlay` error by utilizing standard window framing (`frame: true`).
- Verified `npm run electron:dev` starts Vite and Electron cleanly with `strictPort` behavior and environment variable injection for URL mapping.

---

## 2. Component Architecture

```
src/
├── types/
│   └── index.ts              ← TypeScript interfaces (Chain, Employee, Metric, ErrorTrend…)
│
├── services/
│   ├── mockData.ts           ← 25 employees, 5 errors, metrics for all 3 chains
│   └── api.ts                ← Service abstraction (DashboardService, EmployeeService)
│
├── components/
│   ├── layout/
│   │   ├── Layout.tsx        ← Sidebar + TopHeader + main content wrapper
│   │   ├── TopHeader.tsx     ← Compact header: title / refresh / settings / last updated
│   │   └── TitleBar.tsx      ← Frameless Electron custom title bar (disabled for stability)
│   │
│   ├── dashboard/
│   │   ├── PageHeader.tsx        ← Title + subtitle + optional right slot
│   │   ├── SectionHeader.tsx     ← Label with accent bar
│   │   ├── TimeRangeSelector.tsx ← 24h / 7d / 30d segmented control
│   │   ├── MetricCard.tsx        ← KPI card with label, value, change%, sparkline
│   │   ├── TaskDistribution.tsx  ← Donut chart + legend (status breakdown)
│   │   ├── TrendChart.tsx        ← Multi-type chart (Line/Area/Bar/Stacked) with switcher
│   │   └── ChainOverviewTable.tsx ← Summary table for global dashboard → links to chain pages
│   │
│   └── ui/
│       ├── Badge.tsx             ← Success / warning / error / info / default variants
│       └── States.tsx            ← LoadingState / EmptyState / ErrorState
│
└── pages/
    ├── Dashboard.tsx   ← Global + per-chain dashboard (same component)
    ├── Employees.tsx   ← Table with search, chain filter, sort, pagination
    └── Analytics.tsx   ← Error breakdown: KPIs + pie + bar by chain + trend chart
```

---

## 3. Design System

### Colors (CSS `@theme` / `oklch` tokens)

| Token | Value | Purpose |
|---|---|---|
| `--color-background` | `oklch(0.12 0.015 250)` | Dark navy base |
| `--color-surface` | `oklch(0.16 0.015 250)` | Card / sidebar |
| `--color-brand-primary` | `oklch(0.55 0.28 160)` | Emerald accent |
| `--color-brand-secondary` | `oklch(0.65 0.15 220)` | Cyan |
| `--color-status-success` | `oklch(0.6 0.18 140)` | Green |
| `--color-status-warning` | `oklch(0.7 0.2 70)` | Amber |
| `--color-status-error` | `oklch(0.6 0.2 25)` | Red |
| `--color-status-info` | `oklch(0.6 0.15 250)` | Blue |

### Typography
- Font: `Inter`, system-ui fallback
- Base size: `0.875rem` (dense UI)
- Labels: `10–11px`, uppercase, tracked, tabular-nums for numeric values

### Chart Theming (Recharts)
- Dark transparent background, no default white fills
- Subtle `var(--color-border)` grid lines, no vertical gridlines
- Custom `Tooltip` using surface colors
- Smooth gradients for Area chart fills
- `radius={[3,3,0,0]}` on Bar charts (minimal rounding)

---

## 4. Mock Data Architecture

All data is isolated in `src/services/mockData.ts`:

- **25 employees** spread across FPT Shop (10), Long Châu (9), Vaccine (6)
- **5 errors** with varying types and statuses
- **Sparklines** procedurally generated per metric (stable seeded values in the future)
- **Chain summaries** precomputed per chain as `Record<Chain, ChainSummary>`
- **ErrorTrends** 7-point historical series

Services (`src/services/api.ts`) simulate async API calls with `setTimeout` delay so loading states activate.

---

## 5. Electron Readiness

| Item | Status |
|---|---|
| `electron/main.cjs` — main process | ✅ Written |
| `electron/preload.cjs` — context bridge | ✅ Written |
| `package.json main` field | ✅ Set to `electron/main.cjs` |
| `vite.config.ts base: './'` | ✅ Relative paths for file:// loading |
| `electron:dev` script | ✅ `concurrently vite + wait-on + electron` |
| `electron:build` script | ✅ `vite build + electron-builder` |
| electron-builder NSIS config | ✅ Win x64 installer |
| TitleBar (native frame) | ✅ Set to `frame: true` for OS stability |
| contextIsolation / sandbox | ✅ Enabled |

### To run in Electron dev mode:
```bash
cd dashboard-app
npm run electron:dev
```

### To build installable `.exe`:
```bash
npm run electron:build
# Output: dashboard-app/release/
```

---

## 6. Future Backend Integration (Phase 2)

The Python FastAPI backend will slot in cleanly:

```
Electron
  └─ React (this codebase)
       └─ src/services/api.ts   ← only file to change
            └─ fetch('http://localhost:8000/api/...')
                 └─ Python FastAPI
                      └─ Internal data sources
```

**IPC path for Phase 2:**
- `electron/preload.cjs` exposes `window.opsMonitor.invoke('endpoint', params)`
- `electron/main.cjs` handles IPC → spawns / communicates with Python subprocess
- `src/services/api.ts` replaces `delay()` mocks with `window.opsMonitor.invoke()` calls

Planned API endpoints already typed in `src/types/index.ts`:
- `GET /api/dashboard/summary?chain=...`
- `GET /api/dashboard/trends?chain=...&range=...`
- `GET /api/employees?chain=...`
- `GET /api/errors/analytics`

---

## 7. Remaining Work (Phase 2+)

| Item | Phase |
|---|---|
| Python FastAPI backend | 2 |
| Real data sources (scraping / DB / Excel) | 2 |
| Authentication & role-based access | 2 |
| Employee detail side panel / page | 2 |
| History / Lịch sử page | 2 |
| Settings page | 2 |
| Electron IPC bridge to Python | 2 |
| Real-time WebSocket error notifications | 2 |
| Python subprocess management in Electron | 2 |
| `electron-builder` icon assets (`public/icon.ico`) | Before packaging |
| Code splitting (chunk > 500KB warning) | Optimization |
| E2E tests (Playwright) | QA |

---

## 8. Known Limitations (Phase 1)

- **Mock data only** — no persistence between sessions
- **Sparklines use random values** — will be deterministic when backed by real API
- **Electron title bar buttons** are now handled by standard OS window Chrome (`frame:true`).
- **Bundle size 730KB** — acceptable for Electron, can be split in Phase 2
- **No icon.ico** — packaging will fail without it; a placeholder must be added before `electron:build`

 # #   P h a s e   2 . 2      C a l l l o g   /   T i c k e t   E r r o r   M o n i t o r i n g   U X / U I 
 
 # # #   B u s i n e s s   C o n t e x t   R e f r a m i n g 
 -   * * P u r p o s e : * *   S h i f t e d   e n t i r e   d a s h b o a r d   d o m a i n   f r o m   g e n e r i c   " d e v i c e / s y s t e m   m o n i t o r i n g "   t o   s p e c i f i c a l l y   m o n i t o r i n g   * * C a l l l o g / T i c k e t   Q u a l i t y * * . 
 -   * * R e m o v e d   C o n c e p t s : * *   C a m e r a ,   D e v i c e ,   S y s t e m   e r r o r ,   H a r d w a r e   e r r o r ,   T a s k   r u n n i n g / p e n d i n g   s t a t u s e s . 
 -   * * N e w   F o c u s : * *   I d e n t i f y i n g   w h i c h   c h a i n s ,   e r r o r   t y p e s   ( e . g .   " T h i �u   t h � n g   t i n " ,   " S a i   n �i   d u n g " ) ,   a n d   e m p l o y e e s   a r e   g e n e r a t i n g   t h e   m o s t   f l a w e d   t i c k e t s . 
 
 # # #   I n f o r m a t i o n   H i e r a r c h y   &   K P I   R e d e s i g n 
 T h e   i n t e r f a c e   w a s   r e s t r u c t u r e d   t o   a n s w e r   s u p e r v i s o r   q u e s t i o n s   i n s t a n t l y : 
 1 .   * * T �N G   L �I   ( H i g h e s t   p r i o r i t y ) : * *   N o w   d i s p l a y s   a s   ` 5 6 p x `   b o l d   t e x t   i n   t h e   ` C a l l l o g K p i B a r ` . 
 2 .   * * T �N G   K I �M   T R A   &   T �  L �  L �I : * *   S e c o n d a r y   K P I s   d i s p l a y e d   h o r i z o n t a l l y   a l o n g s i d e   T o t a l   E r r o r s . 
 3 .   * * L �I   T H E O   C H U �I : * *   ` C a l l l o g C h a i n P a n e l `   s h o w i n g   h o r i z o n t a l   b a r s   w i t h   e x a c t   e r r o r   c o u n t s   a n d   c a l c u l a t e d   e r r o r   r a t e s   p e r   c h a i n . 
 4 .   * * T O P   L O �I   L �I : * *   ` C a l l l o g E r r o r T y p e P a n e l `   r e p l a c e s   g e n e r i c   s y s t e m   e r r o r s ,   s h o w i n g   e x a c t   b u s i n e s s   e r r o r   c a t e g o r i e s . 
 5 .   * * N H � N   V I � N   C �   N H I �U   L �I : * *   ` E m p l o y e e E r r o r R a n k i n g P a n e l `   r e p l a c e s   t h e   g e n e r i c   " C �n   x �  l � "   p a n e l ,   h i g h l i g h t i n g   t r a i n i n g   n e e d s   w i t h o u t   g a m i f y i n g / s h a m i n g . 
 6 .   * * C H I   T I �T   L �I : * *   ` C a l l l o g E r r o r D e t a i l T a b l e `   s h o w i n g   s p e c i f i c   t i c k e t   v i o l a t i o n   n o t e s . 
 
 # # #   A n t i g r a v i t y   K i t   A p p l i c a t i o n 
 -   * * S k i l l   U s e d : * *   ` f r o n t e n d - d e s i g n / s t y l e - b r u t a l i s t . m d `   ( T a c t i c a l   T e l e m e t r y   m o d e ) 
 -   * * A p p l i c a t i o n : * *   R e p l a c e d   h e a v y   r o u n d e d   c a r d s   w i t h   r i g i d   ` b o r d e r   b o r d e r - [ v a r ( - - c o l o r - b o r d e r ) ] `   p a n e l s .   U s e d   ` f o n t - m o n o `   e x t e n s i v e l y   f o r   s m a l l   t r a c k e r   l a b e l s   a n d   r a n k   n u m b e r s   ( ` 0 1 ` ,   ` 0 2 ` ) . 
 -   * * S k i l l   U s e d : * *   ` w e b - d e s i g n - g u i d e l i n e s `   ( A c c e s s i b i l i t y   &   T y p o g r a p h y ) 
 -   * * A p p l i c a t i o n : * *   U s e d   ` t a b u l a r - n u m s `   f o r   a l l   d y n a m i c   d a t a .   S t r i p p e d   o u t   g a m i f i e d   t r e n d   a r r o w s   i n   f a v o r   o f   p u r e   n u m b e r s   w h e r e   a p p r o p r i a t e .   A d d e d   ` a r i a - l a b e l `   t o   a l l   i n t e r a c t i v e   e l e m e n t s . 
 
 # # #   E l e c t r o n   V a l i d a t i o n   &   R e f a c t o r i n g 
 -   * * T y p e s : * *   C o m p l e t e l y   r e w r o t e   ` s r c / t y p e s / i n d e x . t s `   t o   i n t r o d u c e   ` C a l l l o g E r r o r ` ,   ` C a l l l o g O v e r v i e w S u m m a r y ` ,   a n d   ` C h a i n C a l l l o g S t a t s ` .   L e g a c y   t y p e s   m a r k e d   ` @ d e p r e c a t e d `   b u t   k e p t   f o r   ` a p i . t s `   c o m p a t i b i l i t y . 
 -   * * M o c k   D a t a : * *   R e f a c t o r e d   ` m o c k D a t a . t s `   t o   s u p p l y   r e a l i s t i c   C a l l l o g   e r r o r   s c e n a r i o s . 
 -   * * C o m p i l a t i o n : * *   ` n p m   r u n   b u i l d `   e x i t s   0 .   T y p e S c r i p t   v a l i d a t e s   c l e a n . 
 -   * * U X   C o n s t r a i n t   M e t : * *   N o   l a r g e   h i s t o r i c a l   t r e n d   c h a r t s   o n   t h e   m a i n   d a s h b o a r d   ( r e s e r v e d   f o r   A n a l y t i c s ) . 
 -   * * N o   E x t r a   D e p e n d e n c i e s : * *   A c h i e v e d   c o m p l e x   b a r   v i s u a l i z a t i o n s   u s i n g   p u r e   C S S   ( ` w - f u l l   f l e x - 1   t r a n s i t i o n - a l l ` )   i n s t e a d   o f   i m p o r t i n g   h e a v y   c h a r t i n g   l i b r a r i e s . 
  
 