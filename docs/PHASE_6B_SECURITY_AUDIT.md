# BÁO CÁO KIỂM TOÁN AN TOÀN & ĐỘ TIN CẬY HỆ THỐNG — PHASE 6B
## DEEP SECURITY & INTEGRATION RELIABILITY AUDIT REPORT

**Thời gian thực hiện:** 11/11/2026  
**Hệ thống được kiểm toán:**
- Dashboard Web: `DashBoardD/dashboard-app` (React 19 + TypeScript + Vite, cổng dev `5174`)
- Dashboard Backend: `DashBoardD/backend` (FastAPI + SQLite `opsmonitor.db`, cổng `8000`)
- Test Engine Backend: `test/` (FastAPI + Python Services, cổng `127.0.0.1:18020`)
- Điểm vào trung tâm: `#/admin` (Test Operations Control Center) & `#/admin/system` (Quản trị hệ thống)

---

## 1. TÓM TẮT KẾT QUẢ KIỂM TOÁN (EXECUTIVE SUMMARY)

Quá trình kiểm toán chuyên sâu Phase 6B đã thực hiện rà soát độc lập toàn diện trên mã nguồn thực tế và môi trường runtime đang hoạt động, không giả định kết quả của các báo cáo trước.

### Điểm tích cực:
1. **Phân tách hoàn toàn giữa hai Backend:** Backend Test (`127.0.0.1:18020`) và Backend Dashboard (`0.0.0.0:8000`) chạy độc lập trên 2 tiến trình riêng biệt (PID 23724 và PID 17208).
2. **Khả năng chịu lỗi và cô lập sự cố (Fault Isolation):** Khi backend 18020 gặp sự cố hoặc timeout, `testApiClient` xử lý qua cơ chế timeout 10 giây và AbortController; giao diện hiển thị cảnh báo đỏ và cho phép Retry mà không gây crash cây React hay ảnh hưởng đến các phân hệ khác của Dashboard.
3. **Bảo vệ xác thực cốt lõi của Admin:** Các endpoint thay đổi mật khẩu (`/api/admin/change-password`), lấy cấu hình bảo mật TOTP (`/api/admin/totp-config`) và xác thực phiên (`/api/admin/verify`) đều bắt buộc có Bearer Token hợp lệ và trả về `HTTP 401 Unauthorized` nếu không có hoặc dùng token giả mạo.
4. **Bảo toàn dữ liệu 100%:** Tệp cấu hình `admin_config.json` (1,151 bytes) và cơ sở dữ liệu `opsmonitor.db` (27,009,024 bytes) được bảo toàn nguyên vẹn.
5. **Chất lượng mã nguồn:** `npm run lint` đạt 0 lỗi; `npm run build` thành công trong 473ms; 0 lỗi runtime phát sinh trên console trình duyệt.

### Các phát hiện an ninh cần lưu ý (Backend Dashboard 8000):
1. **Endpoint đọc nhạy cảm chưa có xác thực:** `GET /api/inside/creds` trả về thông tin tài khoản Inside không yêu cầu Header Authorization.
2. **Endpoint quản trị & nhật ký công khai:** `GET /api/admin/overview` (thông số phần cứng CPU, RAM, dung lượng DB) và `GET /api/admin/logs` (nhật ký hệ thống) hiện không yêu cầu token xác thực.
3. **Endpoint thay đổi cấu hình ngầm:** `POST /api/auto-sync/config`, `POST /api/auto-sync/run-now` và `DELETE /api/admin/logs` hiện chưa gắn middleware/dependency xác thực token admin ở tầng backend.
4. **Cơ chế Token TTL:** Token admin lưu trong `admin_config.json` không kiểm tra thời hạn hết hạn (`created_at` không được so khớp với thời gian sống tối đa).
5. **Định tuyến:** Route `#/departments` chưa được khai báo trong `App.tsx` nên hiển thị màn hình trắng khi truy cập trực tiếp.

---

## 2. DANH SÁCH ENDPOINT VÀ TRẠNG THÁI XÁC THỰC (API INVENTORY & AUTH MATRIX)

### 2.1. Dashboard Backend (Cổng 8000)

| Endpoint | Method | Phân loại | Yêu cầu Auth ở Backend? | Trạng thái kiểm thử thực tế | Bằng chứng kiểm thử |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `/api/admin/login` | POST | Mutate | Không (Public Login) | **PASS** | Source Audit & Login flow |
| `/api/admin/verify` | POST | Read | **CÓ** (Bearer Token) | **PASS** | API Test: Không token ➔ `HTTP 401`, Token sai ➔ `HTTP 401` |
| `/api/admin/change-password` | POST | Mutate | **CÓ** (Bearer Token) | **PASS** | API Test: Không token ➔ `HTTP 401 (Yêu cầu quyền Admin!)` |
| `/api/admin/totp-config` | GET | Read | **CÓ** (Bearer Token) | **PASS** | API Test: Không token ➔ `HTTP 401 (Yêu cầu quyền Admin!)` |
| `/api/admin/totp-config` | POST | Mutate | **CÓ** (Bearer Token) | **PASS** (Source) | Source Audit: `admin.py:144-151` kiểm tra `valid_tokens` |
| `/api/admin/totp-config/test` | POST | Read | **CÓ** (Bearer Token) | **PASS** (Source) | Source Audit: `admin.py:175-182` kiểm tra `valid_tokens` |
| `/api/admin/overview` | GET | Read | **CHƯA CÓ** | **WARNING** | API Test: Không token vẫn trả về `HTTP 200 (OK)` |
| `/api/admin/logs` | GET | Read | **CHƯA CÓ** | **WARNING** | API Test: Không token vẫn trả về `HTTP 200 (OK)` |
| `/api/admin/logs` | DELETE | Mutate | **CHƯA CÓ** | **WARNING** | Source Audit: `admin.py:317-320` không có auth header |
| `/api/admin/test-sync/fpt` | POST | Mutate | **CHƯA CÓ** | **NOT RUN** (Safety) | Tránh kích hoạt đồng bộ FPT thật khi đang kiểm toán |
| `/api/auto-sync/config` | GET | Read | **CHƯA CÓ** | **INFO** | API Test: Không token trả về `HTTP 200` cấu hình lịch chạy |
| `/api/auto-sync/config` | POST | Mutate | **CHƯA CÓ** | **WARNING** | Source Audit: `auto_sync.py:38-48` không có auth dependency |
| `/api/auto-sync/run-now` | POST | Mutate | **CHƯA CÓ** | **NOT RUN** (Safety) | Tránh kích hoạt đồng bộ nền thật khi đang kiểm toán |
| `/api/inside/creds` | GET | Read | **CHƯA CÓ** | **HIGH RISK** | API Test: Không token vẫn trả về `HTTP 200` chứa username/pass |
| `/api/inside/creds` | POST | Mutate | **CHƯA CÓ** | **WARNING** | Source Audit: `inside.py:65` không có auth dependency |

### 2.2. Test-LC Backend (Cổng 127.0.0.1:18020 — Kiến trúc Local Loopback)

> **Lưu ý kiến trúc:** Backend Test-LC được thiết kế để chỉ chạy cục bộ và lắng nghe duy nhất trên loopback `127.0.0.1`. Do đó, các endpoint không sử dụng header bearer token mà phân quyền theo mạng cục bộ và che dữ liệu nhạy cảm.

| Endpoint | Method | Phân loại | Cơ chế bảo vệ | Trạng thái kiểm thử | Bằng chứng kiểm thử |
| :--- | :---: | :---: | :--- | :---: | :--- |
| `/health` | GET | Read | Public Health | **PASS** | API Test: `HTTP 200` `{"status":"ok"}` |
| `/api/settings` | GET | Read | Mask sensitive data | **PASS** | API Test: `HTTP 200`, `spreadsheet_id` bị che thành `********` |
| `/api/settings` | PUT | Mutate | Local loopback | **PASS** (Source) | Chỉ cho phép ghi đè đường dẫn kho và chu kỳ |
| `/api/camera/warehouse/status` | GET | Read | Read cache | **PASS** | API Test: `HTTP 200`, trả về 3,725 cửa hàng |
| `/api/camera/jobs` | POST | Mutate | Background thread | **NOT RUN** (Safety) | Không chạy ping camera thật |
| `/api/ftel-dvr/status` | GET | Read | Read state | **PASS** | API Test: `HTTP 200`, trạng thái `idle` |
| `/api/ftel-dvr/scan/start` | POST | Mutate | Scanner worker | **NOT RUN** (Safety) | Không chạy scan DVR thật |
| `/api/ticket/data` | GET | Read | Read cached excel | **PASS** (Source) | Source Audit: `ticket_router.py:74` |
| `/api/ticket/jobs` | POST | Mutate | SSC task | **NOT RUN** (Safety) | Không tạo Ticket SSC thật |
| `/api/zalo/status` | GET | Read | Read loop state | **PASS** | API Test: `HTTP 200`, 661 tin, 538 sync |
| `/api/zalo/open-browser` | POST | Mutate | Selenium Chrome | **NOT RUN** (Safety) | Không khởi chạy Selenium Chrome |

---

## 3. KẾT QUẢ KIỂM TRA PHIÊN ĐĂNG NHẬP (ADMIN SESSION SECURITY)

1. **Truy cập `#/admin/system` khi chưa xác thực:**
   - **Kết quả:** **PASS** (Bằng chứng: Browser E2E, screenshot `final_step_4.png`).
   - Giao diện bị khóa hoàn toàn. Toàn bộ các tab quản trị nhạy cảm (AutoSync, TOTP, Logs) và thẻ đo lường phần cứng **hoàn toàn không được mount vào DOM**.
2. **Kiểm tra vòng đời Token (Token Lifecycle):**
   - Lưu trữ: `localStorage.getItem('admin_token')`.
   - Khi tải lại trang: `Admin.tsx` lập tức gọi `POST /api/admin/verify`. Nếu token không hợp lệ hoặc đã bị xóa khỏi `admin_config.json`, token ngay lập tức bị loại bỏ khỏi `localStorage` và giao diện quay về form đăng nhập.
3. **Đăng xuất (Logout):**
   - Hàm `handleLogout()` gọi `localStorage.removeItem('admin_token')` và `setToken(null)`. Phiên làm việc trên client bị hủy ngay lập tức.
4. **Đánh giá rủi ro lưu trữ `localStorage`:**
   - `localStorage` dễ bị tấn công qua kịch bản XSS nếu ứng dụng có lỗ hổng chèn script.
   - Giải pháp khuyến nghị cho tương lai: Chuyển sang cơ chế `HttpOnly, Secure, SameSite=Strict` Cookie để hoàn toàn ngăn ngừa JavaScript phía client đọc token.
5. **Thời gian sống của Token (TTL):**
   - `admin_config.json` lưu mảng `active_tokens` với cấu trúc `[{"token": "...", "created_at": ...}]` (giữ tối đa 10 token gần nhất).
   - Tuy nhiên, trong `backend/app/api/admin.py:89`, backend chỉ kiểm tra xem chuỗi token có nằm trong mảng hay không mà **chưa so sánh `created_at` với một ngưỡng thời gian hết hạn cố định (ví dụ: 8 giờ)**. Do đó, một token có thể tồn tại lâu dài nếu chưa có 10 phiên đăng nhập mới đẩy nó ra khỏi mảng.
6. **Thời điểm tải dữ liệu (Prefetching Timing):**
   - Khi `token` có giá trị trong `localStorage`, giao diện gọi đồng thời `verify()`, `fetchOverview()` và `fetchLogs()`. Do `overview` và `logs` hiện chưa có rào chắn auth ở backend, hai API này sẽ phản hồi trước khi `verify` hoàn tất.

---

## 4. KẾT QUẢ KIỂM TRA ĐỘ TIN CẬY & CÔ LẬP LỖI GIỮA HAI BACKEND

1. **Khởi tạo độc lập:**
   - Backend Dashboard: Chạy bằng `uvicorn app.main:app` trên cổng `8000` (PID 17208).
   - Backend Test Engine: Chạy độc lập qua launcher `run_standalone_backend.py` trên cổng `18020` (PID 23724).
   - Hai backend không chia sẻ cơ sở dữ liệu, không chia sẻ biến môi trường và không dùng chung event loop.
2. **Cơ chế xử lý Timeout & Lỗi kết nối:**
   - File `dashboard-app/src/services/testApi/client.ts` trang bị `AbortController` với thời gian chờ mặc định `timeout = 10000ms`.
   - Nếu backend 18020 ngắt kết nối hoặc lỗi mạng (`Failed to fetch`), hàm `testApiClient` bắt ngoại lệ và trả về:
     ```json
     {
       "success": false,
       "status": "error",
       "message": "Không thể kết nối đến Test Engine Backend (18020). Vui lòng đảm bảo backend đang chạy."
     }
     ```
   - Cơ chế này không ném `unhandled promise rejection`, ngăn ngừa hoàn toàn hiện tượng sập cây React (React Error Boundary crash).
3. **Trạng thái giao diện khi backend Test offline:**
   - Trong `TestControlCenterPage.tsx`: Khi `healthInfo.online === false`, giao diện hiển thị:
     - Badge màu đỏ: `Test Backend: Ngắt kết nối`
     - Thẻ đo lường: Hiển thị chữ `Offline` thay vì dữ liệu lỗi
     - Banner cảnh báo: Nêu rõ hướng dẫn khởi chạy file `scripts/start_backend.bat`
     - Nút Retry: Cho phép người dùng bấm thử kết nối lại bất cứ lúc nào.
4. **Cô lập lỗi hệ thống:**
   - Các trang Dashboard gốc (`/dashboard`, `/fpt-shop`, `/long-chau`, `/vaccine`, `/employees`, `/analytics`) hoàn toàn không gọi sang port 18020.
   - Do đó, nếu Test backend 18020 sập, toàn bộ DashboardD vẫn vận hành bình thường 100%.

---

## 5. KẾT QUẢ KIỂM TRA HỒI QUY (REGRESSION) VÀ BUILD/LINT

### 5.1. Kiểm tra Linter & Build
- **Linter (`oxlint`):** `PASS` (Quét 60 tệp tin trong 174ms, **0 lỗi**, 138 cảnh báo cũ của Dashboard gốc).
- **TypeScript & Vite Build (`tsc -b && vite build`):** `PASS` (Biên dịch 1,940 modules thành công trong **512ms**, **0 lỗi**).

### 5.2. Kiểm tra điều hướng các Route trên Trình duyệt

| URL Route | Kết quả kiểm thử | Hành vi quan sát được | Bằng chứng |
| :--- | :---: | :--- | :--- |
| `http://localhost:5174/#/` | **PASS** | Tự động chuyển hướng đến `#/dashboard`, render đầy đủ KPI 3 chuỗi | Browser E2E |
| `http://localhost:5174/#/analytics` | **PASS** | Render view Phân tích lỗi, bộ lọc nâng cao | Browser E2E |
| `http://localhost:5174/#/employees` | **PASS** | Render danh sách nhân sự (37 nhân viên), role pills | Browser E2E |
| `http://localhost:5174/#/admin` | **PASS** | Render Test Operations Control Center (61ms latency, 3,725 shops, 6 cards) | Browser E2E |
| `http://localhost:5174/#/admin/camera` | **PASS** | Render Check Camera & DVR, thiết bị monitoring | Browser E2E |
| `http://localhost:5174/#/admin/ticket` | **PASS** | Render Ticket SSC, panel cấu hình sự vụ | Browser E2E |
| `http://localhost:5174/#/admin/motion` | **PASS** | Render Motion Analytics | Browser E2E |
| `http://localhost:5174/#/admin/zalo` | **PASS** | Render Zalo Monitor (661 tin nhắn, trạng thái giám sát) | Browser E2E |
| `http://localhost:5174/#/admin/settings` | **PASS** | Render Cài đặt hệ thống Test | Browser E2E |
| `http://localhost:5174/#/admin/system` | **PASS** | Render form đăng nhập bảo mật Admin System | Browser E2E |
| `http://localhost:5174/#/test` | **PASS** | Tự động redirect sang `http://localhost:5174/#/admin` | Browser E2E |
| `http://localhost:5174/#/test/camera` | **PASS** | Tự động redirect sang `http://localhost:5174/#/admin/camera` | Browser E2E |
| `http://localhost:5174/#/departments` | **INFO / DEFECT** | **Màn hình trắng (Blank Screen)**: Do route chưa được định nghĩa trong `App.tsx` | Browser E2E |

---

## 6. DANH MỤC CÁC RỦI RO CÒN TỒN TẠI VÀ ĐỀ XUẤT KHẮC PHỤC

| Mức độ | Mã rủi ro | Vị trí phát hiện | Mô tả rủi ro | Bằng chứng | Đề xuất khắc phục (Chờ duyệt) |
| :---: | :---: | :--- | :--- | :--- | :--- |
| **P1 (Cao)** | `SEC-01` | `DashBoardD/backend/app/api/inside.py:33` | Endpoint `GET /api/inside/creds` trả về username và password tài khoản Inside dạng plaintext mà không yêu cầu Header Authorization. | API Test: `curl http://127.0.0.1:8000/api/inside/creds` trả về HTTP 200 kèm password | Bổ sung dependency xác thực Admin hoặc chỉ cho phép gọi nội bộ. |
| **P1 (Cao)** | `SEC-02` | `DashBoardD/backend/app/api/auto_sync.py:38` | `POST /api/auto-sync/config` và `POST /api/auto-sync/run-now` cho phép thay đổi lịch chạy ngầm và kích hoạt đồng bộ mà không kiểm tra quyền Admin. | Source Audit: Không có tham số `authorization: Header(None)` | Bổ sung dependency xác thực `verify_admin_token` vào router `auto_sync`. |
| **P2 (Trung bình)** | `SEC-03` | `DashBoardD/backend/app/api/admin.py:304` | `GET /api/admin/logs` và `DELETE /api/admin/logs` cho phép đọc và xóa sạch log server port 8000 công khai. | API Test: `curl http://127.0.0.1:8000/api/admin/logs` trả về HTTP 200 | Thêm kiểm tra `Header(None)` và đối soát `active_tokens`. |
| **P2 (Trung bình)** | `SEC-04` | `DashBoardD/backend/app/api/admin.py:199` | `GET /api/admin/overview` trả về thông số CPU, RAM, dung lượng SQLite mà không cần token. | API Test: `curl http://127.0.0.1:8000/api/admin/overview` trả về HTTP 200 | Thêm kiểm tra xác thực trước khi trả về metrics chi tiết. |
| **P2 (Trung bình)** | `SEC-05` | `DashBoardD/backend/app/api/admin.py:89` | Token Admin trong `admin_config.json` không có cơ chế hết hạn theo thời gian (TTL). | Source Audit: Chỉ so sánh `token in valid_tokens`, không tính toán `created_at` | Bổ sung kiểm tra `time.time() - t["created_at"] < 28800` (8 tiếng). |
| **P3 (Thấp)** | `UI-01` | `DashBoardD/dashboard-app/src/App.tsx` | Route `#/departments` chưa được đăng ký trong hệ thống router, dẫn tới màn hình trắng nếu người dùng gõ trực tiếp URL này. | Browser E2E: DOM `#root` rỗng | Bổ sung route điều hướng hoặc chuyển hướng về `#/dashboard`. |

---

## 7. DANH SÁCH CÁC BÀI TEST CHƯA CHẠY VÀ LÝ DO (TESTS NOT RUN)

1. **Thao tác ngắt tiến trình (Kill Process) để mô phỏng sự cố Backend 8000 hoặc 18020:**
   - **Trạng thái:** `NOT RUN`
   - **Lý do:** Tuân thủ quy tắc Mục 5 ("Không tự tắt tiến trình backend đang được người dùng sử dụng. Không thực hiện kiểm thử bằng cách kill process hoặc thay đổi cổng khi chưa có môi trường kiểm thử an toàn được xác nhận").
2. **Kích hoạt luồng quét camera thật (`POST /api/camera/jobs`):**
   - **Trạng thái:** `NOT RUN`
   - **Lý do:** Tránh gây tải mạng ping liên tục đến các dải IP thiết bị camera của cửa hàng.
3. **Kích hoạt tự động tạo Ticket SSC (`POST /api/ticket/jobs`):**
   - **Trạng thái:** `NOT RUN`
   - **Lý do:** Tránh tạo các sự vụ rác thật trên hệ thống SSC portal của doanh nghiệp.
4. **Mở trình duyệt Selenium và cào tin nhắn Zalo (`POST /api/zalo/open-browser`):**
   - **Trạng thái:** `NOT RUN`
   - **Lý do:** Tuân thủ quy tắc không can thiệp vào tài khoản Zalo đang đăng nhập thực tế.
5. **Thử nghiệm xóa sạch log (`DELETE /api/admin/logs`) hoặc kích hoạt đồng bộ nền (`POST /api/auto-sync/run-now`):**
   - **Trạng thái:** `NOT RUN`
   - **Lý do:** Tránh làm mất nhật ký chẩn đoán và tránh làm sai lệch dữ liệu trong `opsmonitor.db`.

---

## 8. BẢNG THEO DÕI TÍNH TOÀN VẸN VÀ TỆP TIN THAY ĐỔI

### Trạng thái Git & Dữ liệu:
- **Tệp `backend/app/admin_config.json`:** Bảo toàn nguyên vẹn (Last modified: 11/11/2026 00:44:08).
- **Cơ sở dữ liệu `opsmonitor.db`:** Bảo toàn nguyên vẹn (Kích thước: 27,009,024 bytes).
- **Mã nguồn Backend Python:** Không chỉnh sửa logic nghiệp vụ nào trong Phase 6B.

### Danh sách tệp tin thực tế trong phiên làm việc:
1. `dashboard-app/src/App.tsx`: Tái cấu trúc routing, đưa admin vào Layout chung, đăng ký redirect `test/*`.
2. `dashboard-app/src/components/layout/Layout.tsx`: Ẩn mục quản trị trên Sidebar theo yêu cầu của người dùng, cập nhật tiêu đề ngữ cảnh.
3. `dashboard-app/src/pages/test/TestControlCenterPage.tsx`: Trang tổng quan điều khiển Test Operations.
4. `dashboard-app/src/pages/test/index.ts`: Xuất component Control Center.
5. `dashboard-app/src/pages/Admin.tsx`: Tinh chỉnh nút quay về Test Control Center.
6. `DashBoardD/docs/PHASE_6B_SECURITY_AUDIT.md`: Tệp tài liệu báo cáo kiểm toán này.

---

## 9. ĐIỀU KIỆN KẾT THÚC & DỪNG BƯỚC

Theo đúng quy định tại **Mục 9**:
- Hệ thống **dừng hoàn toàn tại đây** sau khi phát hành báo cáo kiểm toán Phase 6B.
- Không tự ý sửa các lỗ hổng đã phát hiện (`SEC-01`, `SEC-02`,...).
- Không tạo script 1-click hoặc dọn dẹp file.
- Chờ ý kiến phê duyệt và chỉ đạo của người dùng trước khi thực hiện bất kỳ hành động tiếp theo nào!
