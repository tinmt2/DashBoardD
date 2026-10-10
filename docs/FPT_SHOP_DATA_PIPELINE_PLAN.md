# FPT SHOP DATA IMPORT PIPELINE PLAN

## 1. Existing Architecture
- **Frontend**: Electron + React + Vite application (`dashboard-app`).
- **Backend**: Currently, there is no Python backend implementation found in the repository. The data logic is mocked in the frontend (`src/services/mockData.ts`).
- **Dashboard UI**: ALREADY FINALIZED, using GlassCard, Layout, Badge, and States components. The frontend relies heavily on types defined in `src/types/index.ts`.

## 2. Existing Reusable Components
- **Types**: `Chain`, `CalllogErrorType`, `CalllogError`, `Employee`, `CalllogOverviewSummary` in `src/types/index.ts`.
- **UI Components**: `GlassCard`, `Badge`, `States`, `Layout` and existing navigation/table components in `src/components`.

## 3. FPT Excel Structure
Currently, no raw Excel file is provided in the repository. Based on the requirements, FPT Shop Excel files may contain varied columns such as:
- "Tên nhân viên", "Nhân viên", "Employee"
- "Mã ticket", "Ticket", "Ticket ID"
- "Mã shop", "Shop Code"
- "Ngày tạo", "Thời gian tạo"
- "Loại lỗi", "Error Type"
- "Nội dung lỗi", "Lý do lỗi"

The structure is variable, therefore we will implement an adapter to read and map these headers dynamically.

## 4. Proposed Normalized Schema
`TicketRecord` (Python Pydantic Model):
```python
class TicketRecord(BaseModel):
    id: str
    chain: Literal["FPT_SHOP"] = "FPT_SHOP"
    ticket_id: str
    employee_id: Optional[str] = None
    employee_name: str
    shop_code: Optional[str] = None
    shop_name: Optional[str] = None
    created_at: Optional[datetime] = None
    checked_at: Optional[datetime] = None
    error_status: Literal["ERROR", "PASS", "PENDING"]
    error_type: Optional[str] = None
    error_reason: Optional[str] = None
    source: Literal["EXCEL", "INTERNAL_WEB"]
    imported_at: datetime
```

## 5. Mapping Strategy
- Use a dictionary mapping for known column names in the `FPTShopAdapter`.
- If confidence is low, present a `Data Preview / Column Mapping` UI for user confirmation.
- Date and Error Types will be normalized via dedicated parsers (`FPTShopDateParser`, `fpt_shop_error_mapping.py`).

## 6. Login Architecture
- `BrowserSessionManager`: Manage browser automation (Playwright/Selenium) for the FPT Shop internal web.
- `FPTShopWebCollector`: Opens internal web and navigates to the login page.
- **Google Auth Handoff**: If MFA or Google Auth is required, wait for user intervention via the browser. DO NOT store passwords or OTPs.

## 7. API Contract
Backend APIs (FastAPI recommended):
- `POST /api/fpt-shop/import/preview`: Upload Excel, return validation, mapping, and preview data.
- `POST /api/fpt-shop/import/commit`: Commit previewed data.
- `GET /api/fpt-shop/import/history`: Get list of past imports.
- `POST /api/fpt-shop/auth/start`: Start internal web login session.
- `GET /api/fpt-shop/auth/status`: Check authentication status.
- `POST /api/fpt-shop/sync`: Start scraping authorized data.
- `GET /api/fpt-shop/data`: Fetch normalized FPT Shop data.
- `GET /api/fpt-shop/summary`: Fetch dashboard summary metrics.

## 8. Files to Create
**Backend**:
- `backend/app/services/importers/fpt_shop/importer.py`
- `backend/app/services/importers/fpt_shop/mapper.py`
- `backend/app/services/importers/fpt_shop/validator.py`
- `backend/app/services/importers/fpt_shop/schema.py`
- `backend/app/services/importers/fpt_shop/fpt_shop_error_mapping.py`
- `backend/app/services/collectors/fpt_shop/login.py`
- `backend/app/services/collectors/fpt_shop/browser.py`
- `backend/app/services/collectors/fpt_shop/collector.py`
- `backend/app/models/ticket.py`, `error.py`, `employee.py`
- `backend/app/api/fpt_shop.py`

**Frontend**:
- `src/pages/FPTShop/FPTShopData.tsx`
- `src/pages/FPTShop/FPTShopImport.tsx`
- `src/pages/FPTShop/FPTShopLogin.tsx`

## 9. Files to Modify
- `dashboard-app/src/App.tsx` or routes file (to add FPT Shop pages).
- `dashboard-app/src/components/layout/Layout.tsx` (to add sidebar links if necessary).
- Dashboard data fetching services (to consume new API for FPT Shop instead of mockData where applicable).

## 10. Files that must NOT be modified
- `src/types/index.ts` (Keep current dashboard contract).
- Existing Dashboard UI component files (`GlassCard.tsx`, `Dashboard.tsx` etc.), unless explicitly required.
- Do NOT touch/create Long Chau or Vaccine integrations.
