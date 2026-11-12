# BÁO CÁO KHẮC PHỤC LỖI BẢO MẬT & ROUTING (PHASE 6C.1)

**Thời gian thực hiện:** 11/11/2026  
**Dự án:** `DashBoardD` tích hợp module `Test-LC`  
**Chuyên môn áp dụng:** Security Auditor & Full-Stack System Architect  
**Trạng thái chung:** **HOÀN THÀNH TOÀN DIỆN (ALL PASS)**

---

## 1. MỤC TIÊU & PHẠM VI TRIỂN KHAI

Giai đoạn Phase 6C.1 thực hiện khắc phục có kiểm soát các lỗ hổng an ninh xác thực và lỗi giao diện đã được phát hiện trong đợt kiểm toán Phase 6B:
- **SEC-01:** Rò rỉ thông tin đăng nhập Inside Account (`/api/inside/creds`).
- **SEC-02:** Thay đổi cấu hình và kích hoạt tiến trình tự động đồng bộ ngầm trái phép (`/api/auto-sync/config`, `/api/auto-sync/run-now`).
- **SEC-03:** Truy cập và làm trống nhật ký hệ thống không qua xác thực (`/api/admin/logs`).
- **SEC-04:** Tiết lộ thông số hạ tầng máy chủ (`/api/admin/overview`) và kích hoạt chạy thử (`/api/admin/test-sync/fpt`).
- **SEC-05:** Token xác thực Admin không có thời hạn hết hạn (TTL) và thiếu cơ chế thu hồi token phía máy chủ (Server-side Revocation on Logout).
- **ROUTE DEFECT:** Lỗi màn hình trắng khi truy cập tuyến `#/departments`.

### Tuân thủ nguyên tắc an toàn:
1. **Bảo toàn dữ liệu:** Giữ nguyên vẹn cơ sở dữ liệu `DashBoardD/backend/opsmonitor.db` (kích thước chính xác: **27,009,024 bytes**).
2. **Bảo toàn cấu hình:** Giữ nguyên mật khẩu hash, tài khoản và khóa TOTP bí mật trong `admin_config.json`.
3. **Không tạo tác vụ nghiệp vụ thật:** Tuyệt đối không tạo ticket SSC, không quét camera/DVR, không kích hoạt Selenium ChromeDriver, không ghi đè Google Sheets, không mutate Zalo.
4. **Không cài đặt thư viện ngoài:** Không bổ sung bất kỳ npm package hoặc python package mới nào ngoài môi trường hiện hữu.

---

## 2. KẾT QUẢ KHẮC PHỤC CHI TIẾT

| Mã kiểm toán | Mức độ | Trạng thái trước khắc phục | Giải pháp triển khai | Trạng thái sau khắc phục |
| :--- | :--- | :--- | :--- | :--- |
| **SEC-01** | High | `GET/POST /api/inside/creds` công khai, trả về plaintext username/password | Tích hợp `verify_admin_token` kiểm tra Bearer token; cập nhật frontend `insideApi.ts` đính kèm token | **ĐÃ KHẮC PHỤC (PASS)**<br>Chặn 401 khi không có token |
| **SEC-02** | High | `POST /api/auto-sync/config` & `POST /api/auto-sync/run-now` không yêu cầu quyền Admin | Tích hợp `verify_admin_token` trên các mutation routes; cập nhật `autoSyncApi.ts` đính kèm token | **ĐÃ KHẮC PHỤC (PASS)**<br>Chặn 401 mọi hành vi ghi đè trái phép |
| **SEC-03** | High | `GET/DELETE /api/admin/logs` công khai lộ stack trace và cho phép xóa sạch log bộ nhớ | Yêu cầu `verify_admin_token` cho cả GET và DELETE; cập nhật `Admin.tsx` đính kèm Authorization header | **ĐÃ KHẮC PHỤC (PASS)**<br>Chặn 401 truy cập/xóa log |
| **SEC-04** | Medium | `GET /api/admin/overview` & `POST /api/admin/test-sync/fpt` công khai lộ CPU/RAM/DB | Yêu cầu `verify_admin_token`; cập nhật `Admin.tsx` truyền token trong `fetchOverview` và `handleTestSyncFpt` | **ĐÃ KHẮC PHỤC (PASS)**<br>Chặn 401 nếu chưa đăng nhập Admin |
| **SEC-05** | Medium | Token Admin tồn tại vĩnh viễn, đăng xuất chỉ xóa token ở client | Xây dựng module `auth.py` áp dụng TTL 8 giờ (28,800s), tự động lọc bỏ token hết hạn, bổ sung endpoint `POST /api/admin/logout` thu hồi token tức thì | **ĐÃ KHẮC PHỤC (PASS)**<br>Token tự hết hạn; thu hồi token thành công |
| **ROUTE DEFECT** | Low | Tuyến `#/departments` hiển thị màn hình trắng do chưa đăng ký route trong `App.tsx` | Khai báo route redirect `departments -> /employees` và bổ sung route fallback toàn cục `* -> /dashboard` | **ĐÃ KHẮC PHỤC (PASS)**<br>Redirect mượt mà, render 100% UI |

---

## 3. CHI TIẾT MÃ NGUỒN ĐÃ CHỈNH SỬA

### 3.1. Backend Python (`DashBoardD/backend`)
1. **Tạo module xác thực tập trung:** [`backend/app/core/auth.py`](file:///D:/T%C3%ADn/ABC/DashBoardD/backend/app/core/auth.py)
   - Hàm `get_admin_config()` & `save_admin_config()`: Quản lý đọc ghi tệp cấu hình thread-safe.
   - Hàm `verify_admin_token(authorization)`: Trích xuất Bearer token, đối chiếu danh sách `active_tokens`, kiểm tra thời hạn sống của token (`ADMIN_TOKEN_TTL_SECONDS = 8 * 3600`). Tự động dọn dẹp các token đã quá hạn khỏi tệp cấu hình và trả về mã lỗi HTTP 401 nếu không hợp lệ.
   - Hàm `revoke_admin_token(token)`: Xóa bỏ token khỏi danh sách `active_tokens` khi người dùng đăng xuất.
2. **Cập nhật:** [`backend/app/api/admin.py`](file:///D:/T%C3%ADn/ABC/DashBoardD/backend/app/api/admin.py)
   - Đưa `verify_admin_token` vào các endpoint: `/verify`, `/change-password`, `/totp-config`, `/overview`, `/logs` (GET & DELETE), `/test-sync/fpt`.
   - Bổ sung endpoint `POST /logout` cho phép máy chủ thu hồi token ngay khi đăng xuất.
3. **Cập nhật:** [`backend/app/api/auto_sync.py`](file:///D:/T%C3%ADn/ABC/DashBoardD/backend/app/api/auto_sync.py)
   - Bảo vệ `POST /config` và `POST /run-now` bằng `verify_admin_token(authorization)`.
4. **Cập nhật:** [`backend/app/api/inside.py`](file:///D:/T%C3%ADn/ABC/DashBoardD/backend/app/api/inside.py)
   - Bảo vệ `GET /creds` và `POST /creds` bằng `verify_admin_token(authorization)`.

### 3.2. Frontend React (`DashBoardD/dashboard-app`)
1. **Cập nhật:** [`dashboard-app/src/services/insideApi.ts`](file:///D:/T%C3%ADn/ABC/DashBoardD/dashboard-app/src/services/insideApi.ts)
   - Đính kèm header `Authorization: Bearer ${token}` từ `localStorage.getItem('admin_token')`.
2. **Cập nhật:** [`dashboard-app/src/services/autoSyncApi.ts`](file:///D:/T%C3%ADn/ABC/DashBoardD/dashboard-app/src/services/autoSyncApi.ts)
   - Đính kèm Bearer token cho `updateAutoSyncConfig` và `triggerAutoSyncRunNow`.
3. **Cập nhật:** [`dashboard-app/src/pages/Admin.tsx`](file:///D:/T%C3%ADn/ABC/DashBoardD/dashboard-app/src/pages/Admin.tsx)
   - Đính kèm Bearer token cho `fetchOverview`, `fetchLogs`, `handleClearLogs`, `handleTestSyncFpt`.
   - Trong `handleLogout`, kích hoạt gọi `POST /api/admin/logout` để thu hồi token phía backend trước khi xóa `localStorage`.
4. **Cập nhật:** [`dashboard-app/src/App.tsx`](file:///D:/T%C3%ADn/ABC/DashBoardD/dashboard-app/src/App.tsx)
   - Thêm `<Route path="departments" element={<Navigate to="/employees" replace />} />`.
   - Thêm tuyến phòng thủ toàn cục `<Route path="*" element={<Navigate to="/dashboard" replace />} />`.

---

## 4. BẰNG CHỨNG KIỂM THỬ XÁC MINH

### 4.1. Bằng chứng kiểm thử API tự động (API Test Suite)
Đã chạy bộ kịch bản kiểm thử bảo mật `test/scratch/test_security_remediation.py`:
```
--- 1. SEC-01 Tests ---
GET /api/inside/creds (no token): status=401, body={"detail":"Chưa có token xác thực!"} -> PASS
POST /api/inside/creds (no token): status=401, body={"detail":"Chưa có token xác thực!"} -> PASS
GET /api/inside/creds (invalid token): status=401, body={"detail":"Phiên đăng nhập Admin đã hết hạn hoặc không hợp lệ!"} -> PASS

--- 2. SEC-02 Tests ---
POST /api/auto-sync/config (no token): status=401, body={"detail":"Chưa có token xác thực!"} -> PASS
POST /api/auto-sync/run-now (no token): status=401, body={"detail":"Chưa có token xác thực!"} -> PASS
POST /api/auto-sync/config (invalid token): status=401, body={"detail":"Phiên đăng nhập Admin đã hết hạn hoặc không hợp lệ!"} -> PASS

--- 3. SEC-03 Tests ---
GET /api/admin/logs (no token): status=401, body={"detail":"Chưa có token xác thực!"} -> PASS
DELETE /api/admin/logs (no token): status=401, body={"detail":"Chưa có token xác thực!"} -> PASS
GET /api/admin/logs (invalid token): status=401, body={"detail":"Phiên đăng nhập Admin đã hết hạn hoặc không hợp lệ!"} -> PASS

--- 4. SEC-04 Tests ---
GET /api/admin/overview (no token): status=401, body={"detail":"Chưa có token xác thực!"} -> PASS
POST /api/admin/test-sync/fpt (no token): status=401, body={"detail":"Chưa có token xác thực!"} -> PASS
GET /api/admin/overview (invalid token): status=401, body={"detail":"Phiên đăng nhập Admin đã hết hạn hoặc không hợp lệ!"} -> PASS

--- 5. SEC-05 Tests (TTL & Logout) ---
POST /api/admin/verify (valid token): status=200, body={"valid":true,"username":"admin"} -> PASS
GET /api/admin/overview (valid token): status=200, ok=True -> PASS
GET /api/admin/logs (valid token): status=200, ok=True -> PASS

--- 6. Logout Revocation Test ---
Pre-logout verify temp_token: status=200 -> PASS
POST /api/admin/logout: status=200, body={"success":true,"message":"Đã đăng xuất phiên làm việc!"} -> PASS
Post-logout verify temp_token: status=401, body={"detail":"Phiên đăng nhập Admin đã hết hạn hoặc không hợp lệ!"} -> PASS
Verify expired token (TTL > 8h): status=401, body={"detail":"Phiên đăng nhập Admin đã hết hạn hoặc không hợp lệ!"} -> PASS
```

### 4.2. Bằng chứng kiểm thử giao diện thực tế (Browser E2E)
Subagent `Remediation Verifier` đã điều khiển trình duyệt headless kiểm chứng thực tế tại `http://localhost:5174`:
1. **Kiểm tra tuyến `#/departments`:**
   - URL truy cập: `http://localhost:5174/#/departments`
   - URL quan sát thực tế: `http://localhost:5174/#/employees` (chuyển hướng tức thì).
   - Giao diện: Hiển thị đầy đủ bảng "Quản lý nhân viên", số liệu nhân sự ("Tổng: 37", "FPT Shop: 8", "Long Châu: 20", "Vaccine: 9"), thanh tìm kiếm và bộ lọc danh sách nhân viên. Hoàn toàn không có màn hình trắng hay crash.
2. **Kiểm tra Test Control Center (`#/admin`):**
   - URL quan sát thực tế: `http://localhost:5174/#/admin`
   - Giao diện: Hiển thị đầy đủ thanh Tabs điều hướng (Tổng quan Test, Check Camera, Ticket SSC, Motion Analytics, Zalo Monitor, Cài đặt Test, Quản trị Hệ thống).
   - Thẻ dịch vụ hiển thị Test Backend online (127.0.0.1:18020), cơ sở dữ liệu shop (3,725 cửa hàng), các module vận hành ổn định.
3. **Kiểm tra Quản trị hệ thống (`#/admin/system`):**
   - URL quan sát thực tế: `http://localhost:5174/#/admin/system`
   - Giao diện: Hiển thị form đăng nhập Admin chuyên dụng (trường Tài khoản, Mật khẩu, nút Đăng nhập và nút quay lại Tổng quan). Không để lộ thông tin máy chủ ra ngoài giao diện chưa xác thực.
   - Bằng chứng ảnh chụp màn hình ghi nhận: `browser_evidence/dc532462-0824-4346-ac6b-4228db049479/final_step_6.png`.

### 4.3. Bằng chứng kiểm tra biên dịch mã nguồn (Build & Lint)
- **TypeScript & Vite Build:** `tsc -b && vite build` thực thi hoàn tất trong 477ms, trả về **0 lỗi**.
- **Linter:** `oxlint` hoàn tất trong 159ms trên 60 files, trả về **0 lỗi**.

---

## 5. XÁC MINH TOÀN VẸN HỆ THỐNG & DỮ LIỆU

- **Database:** `DashBoardD/backend/opsmonitor.db` dung lượng **27,009,024 bytes**, ngày cập nhật khớp tuyệt đối với nguyên bản.
- **Admin Config:** `DashBoardD/backend/app/admin_config.json` giữ nguyên cấu trúc JSON, mật khẩu băm của quản trị viên và khóa TOTP secret không bị thay đổi.
- **Nghiệp vụ backend Python:** Không có bất kỳ dòng mã nào can thiệp vào logic xử lý camera, DVR, Ticket SSC, Zalo hay đồng bộ Google Sheets.
- **Hạ tầng tiến trình đang chạy:**
  - `DashBoardD` FastAPI Backend: Port `8000` (PID 25220).
  - `Test-LC` FastAPI Backend: Port `18020` (PID 23724).
  - `DashBoardD` Vite Frontend: Port `5174` (PID 11372).

---

## 6. KẾT LUẬN & ĐỀ XUẤT TIẾP THEO

Toàn bộ các phát hiện từ Phase 6B đã được đóng gói và giải quyết dứt điểm trong Phase 6C.1 với đầy đủ bằng chứng đối soát, đạt chuẩn sản xuất (production-ready).

Hệ thống đã sẵn sàng cho bước tiếp theo do Quản trị viên chỉ đạo.
