# BÁO CÁO NGHIỆM THU TÍCH HỢP RUNTIME (PHASE 8.0C)
## LIVE INTEGRATION VERIFICATION & ACCEPTANCE REPORT

**Hệ thống:** DashBoardD & Test Engine  
**Thời gian thực hiện:** 11/11/2026  
**Tính chất giai đoạn:** Nghiệm thu tích hợp độc lập và kiểm tra runtime (Zero Production Code Edit / Zero Side-Effect)  
**Trạng thái nghiệm thu:** **HOÀN TẤT KIỂM TOÁN TĨNH & PHÁT HIỆN CỔNG RUNTIME ĐANG TẮT (BLOCKED FOR LIVE REQUESTS - CHỜ DUYỆT KHỞI ĐỘNG)**

---

## 1. RUNTIME SERVICE STATUS (TRẠNG THÁI TIẾN TRÌNH & CỔNG MẠNG THỰC TẾ)

Theo quy tắc an toàn số 2 và số 8: **Tuyệt đối không tự ý khởi động hoặc bật tiến trình nếu backend đang tắt. Khi phát hiện dịch vụ chưa chạy, ghi nhận BLOCKED và yêu cầu phê duyệt.**

### 1.1. Bảng kiểm toán cổng TCP và tiến trình thực tế
| Cổng (Port) | Dịch vụ tương ứng | Tiến trình phục vụ (PID) | Trạng thái lắng nghe | Health Check Endpoint | Kết quả thăm dò trực tiếp | Phân loại |
| :---: | :--- | :---: | :---: | :--- | :--- | :---: |
| **8000** | DashBoardD Backend | Không có (`None`) | **CLOSED** (Không lắng nghe) | `http://127.0.0.1:8000/api/health` | Connection Failed (Timed out / Refused) | **BLOCKED** |
| **18020** | Test Engine Backend | Không có (`None`) | **CLOSED** (Không lắng nghe) | `http://127.0.0.1:18020/health` | Connection Failed (Timed out / Refused) | **BLOCKED** |
| **5174** | Frontend Dev Server (Vite) | Không có (`None`) | **CLOSED** (Không lắng nghe) | `http://127.0.0.1:5174/` | Connection Failed (Timed out / Refused) | **BLOCKED** |

### 1.2. Bằng chứng thực tế (Command Execution Log)
```powershell
PS D:\Tín\ABC\test> Get-NetTCPConnection -LocalPort 8000, 18020, 5174 -ErrorAction SilentlyContinue
# [Không có kết nối nào đang lắng nghe trên các cổng trên]

PS D:\Tín\ABC\test> netstat -ano | findstr ":8000 :18020 :5174"
# [Không trả về tiến trình nào]

PS D:\Tín\ABC\test> py -3.12 -c "import urllib.request, urllib.error; ..."
DashBoardD Backend Health (http://127.0.0.1:8000/api/health): Connection Failed -> timed out
Test Engine Backend Health (http://127.0.0.1:18020/health): Connection Failed -> timed out
Frontend Dev Server (http://127.0.0.1:5174): Connection Failed -> timed out
```
**Kết luận Nhóm 1:** Cả 2 backend (8000 và 18020) hiện không chạy trong phiên runtime hiện tại. Mọi yêu cầu HTTP mạng trực tiếp đến các cổng này bị **BLOCKED** do dịch vụ offline. Để tiến hành kiểm thử runtime trực tiếp (live calls), cần người dùng phê duyệt lệnh khởi động an toàn.

---

## 2. KIỂM TRA TRIỂN KHAI VÀ BẢO MẬT REVERSE PROXY (CODE & LOGIC AUDIT)

Đã kiểm tra chi tiết mã nguồn triển khai tại [`DashBoardD/backend/app/api/test_proxy.py`](file:///D:/T%C3%ADn/ABC/DashBoardD/backend/app/api/test_proxy.py) và cấu hình router tại [`DashBoardD/backend/app/main.py`](file:///D:/T%C3%ADn/ABC/DashBoardD/backend/app/main.py).

### 2.1. Ma trận tiêu chí Reverse Proxy
| Tiêu chí kỹ thuật | Triển khai thực tế | Đánh giá an toàn | Trạng thái |
| :--- | :--- | :--- | :---: |
| **Tiền tố Route (Prefix)** | `router = APIRouter(prefix="/api/test", tags=["test-proxy"])` | Đăng ký trước catch-all `serve_frontend` trong `main.py` | **PASS** |
| **Host đích Upstream** | `TEST_BACKEND_URL = "http://127.0.0.1:18020"` | Cố định loopback cục bộ, không thể bị giả mạo qua header | **PASS** |
| **Ánh xạ đường dẫn (Mapping)** | Chuẩn hóa `health` -> `/health`, các route khác -> `/api/...` | Phù hợp 100% với router Test Engine | **PASS** |
| **Query String** | `if request.url.query: url = f"{url}?{request.url.query}"` | Giữ nguyên toàn bộ tham số truy vấn | **PASS** |
| **Tước bỏ Authorization** | `EXCLUDED_REQUEST_HEADERS = {"host", "authorization", "cookie"}` | **Bảo mật tuyệt đối**: Token JWT Admin của DashBoardD không bao giờ bị rò rỉ sang Test Engine | **PASS** |
| **Bảo toàn context nghiệp vụ** | Chuyển tiếp các header custom `x-session-id`, `x-action-id`, `x-job-id` | Duy trì khả năng truy vết và tracking log giữa 2 hệ thống | **PASS** |
| **Xử lý Upstream Offline** | Bắt `httpx.ConnectError`, `httpx.ConnectTimeout` -> Trả về `HTTP 503` dạng JSON sạch | Không gây crash backend, không lộ stack trace | **PASS** |
| **Xử lý Timeout** | Timeout 300.0s (connect 5.0s). Bắt `httpx.TimeoutException` -> `HTTP 504` | Hỗ trợ tốt các job xử lý camera nặng, có ngắt kết nối an toàn | **PASS** |
| **Bảo vệ dữ liệu nhạy cảm** | Logger chỉ ghi nhận URL và thông báo lỗi, không in header/token | Không lộ bí mật xác thực ra console/file log | **PASS** |

### 2.2. Bằng chứng kiểm thử Unit Test Proxy độc lập
Đã chạy bộ test cô lập qua `DashBoardD/backend/tests/unit/test_test_proxy.py`:
- `test_proxy_offline_returns_503`: **PASS** (Trả về mã 503 JSON khi port 18020 đóng).
- `test_proxy_mock_success_forwarding`: **PASS** (Xác nhận header `authorization` bị tước bỏ thành công, header `x-session-id` được giữ nguyên).
- `test_proxy_url_mapping_rules`: **PASS** (Xác nhận các quy tắc ánh xạ URL và query params).

---

## 3. BẢNG KIỂM TRA CÁC CHỨC NĂNG GET CỦA TEST (READ-ONLY AUDIT)

Đã đối soát toàn bộ 5 endpoint GET của Test Engine với mã nguồn tại `D:\Tín\ABC\test\app\api\routes\` để xác minh tính **Read-Only** (không gây side-effect):

| Phân hệ / Endpoint | URL Client gọi (Browser) | URL thực tế sau Proxy (Upstream) | Phương thức & Side Effect | Hành vi nội bộ của hàm Backend | Trạng thái Runtime |
| :--- | :--- | :--- | :---: | :--- | :---: |
| **1. Warehouse Status** | `/api/test/api/camera/warehouse/status` | `http://127.0.0.1:18020/api/camera/warehouse/status` | `GET`<br>**Zero Side-Effect** | Gọi `warehouse_sync.get_warehouse_status()`. Đọc trạng thái bộ nhớ đệm kho shop. | **BLOCKED**<br>(Port 18020 tắt) |
| **2. FTEL DVR Status** | `/api/test/api/ftel-dvr/status` | `http://127.0.0.1:18020/api/ftel-dvr/status` | `GET`<br>**Zero Side-Effect** | Đọc dictionary `FTEL_STATE` trong RAM (`status`, `progress`, `total`, `results`). | **BLOCKED**<br>(Port 18020 tắt) |
| **3. Zalo Status** | `/api/test/api/zalo/status?include_messages=false` | `http://127.0.0.1:18020/api/zalo/status?include_messages=false` | `GET`<br>**Zero Side-Effect** | Gọi `zalo_monitor_service.get_full_state()`. Chỉ đọc RAM, không kích hoạt browser. | **BLOCKED**<br>(Port 18020 tắt) |
| **4. Test Settings** | `/api/test/api/settings` | `http://127.0.0.1:18020/api/settings` | `GET`<br>**Zero Side-Effect** | Đọc `get_config()` và tự động che giấu `spreadsheet_id = "********"`. | **BLOCKED**<br>(Port 18020 tắt) |
| **5. Ticket Data** | `/api/test/api/ticket/data?ticket_type=Camera%20MKN` | `http://127.0.0.1:18020/api/ticket/data?ticket_type=Camera%20MKN` | `GET`<br>**Zero Side-Effect** | Gọi `gsheet_sync.read_ticket_sheet()`. Chỉ đọc sheet, không tạo ticket, không ghi dữ liệu. | **BLOCKED**<br>(Port 18020 tắt) |

*Ghi chú cam kết:* Tuyệt đối không gọi bất kỳ endpoint POST nào (`/api/camera/jobs`, `/api/ticket/jobs`, `/api/zalo/open-browser`, `/api/ftel-dvr/jobs`) để bảo vệ hạ tầng vận hành.

---

## 4. BẢNG KIỂM TRA GIAO DIỆN FRONTEND (FRONTEND AUDIT)

Đã kiểm toán mã nguồn React frontend và gói build Production tại `DashBoardD/dashboard-app/dist`:

| Tuyến đường (Route) | File Component tương ứng | Cấu hình API Base URL | Kiểm tra Logic & Validation | Trạng thái UI | Trạng thái Runtime |
| :--- | :--- | :--- | :--- | :---: | :---: |
| **`#/admin`** | `TestControlCenterPage.tsx` | Phân giải tự động qua `getTestApiBaseUrl()` -> `/api/test` | Hiển thị tổng quan các dịch vụ Test, đọc status qua proxy | Sẵn sàng | **BLOCKED**<br>(Server tắt) |
| **`#/admin/camera`** | `CheckCameraPage.tsx` | `/api/test/api/camera` | Đã khôi phục input chọn file `.xlsx/.csv`, thêm badge `Kho: X shop`, hiển thị thông báo lỗi khi thiếu kho thay vì chặn im lặng (`isBlocked`) | Sẵn sàng | **BLOCKED**<br>(Server tắt) |
| **`#/admin/ticket`** | `TicketSSCPage.tsx` | `/api/test/api/ticket` | Đã giảm vòng lặp retry từ 4 xuống 1 (1s delay), hiển thị badge `LỖI KẾT NỐI`, banner cảnh báo và thông báo lỗi theo từng loại ticket | Sẵn sàng | **BLOCKED**<br>(Server tắt) |
| **`#/admin/motion`** | `MotionAnalyticsPage.tsx` | `/api/test/api/motion` | Kiểm tra tải file và bảng phân tích video motion | Sẵn sàng | **BLOCKED**<br>(Server tắt) |
| **`#/admin/zalo`** | `ZaloMonitorPage.tsx` | `/api/test/api/zalo` | Đọc status giám sát Zalo polling | Sẵn sàng | **BLOCKED**<br>(Server tắt) |
| **`#/admin/settings`** | `TestSettingsPage.tsx` | `/api/test/api/settings` | Hiển thị biểu mẫu cấu hình engine Test | Sẵn sàng | **BLOCKED**<br>(Server tắt) |

### 4.1. Kết quả kiểm tra Build Production
- Lệnh: `npm --prefix "D:\Tín\ABC\DashBoardD\dashboard-app" run build`
- Kết quả: **THÀNH CÔNG (0 Lỗi)**
- Bundle sản phẩm: `dist/index.html` (0.69 kB), `dist/assets/index-DXGgMh1K.js` (629.44 kB), `dist/assets/index-BNMxGWLU.css` (135.40 kB).

---

## 5. HỒI QUY HỆ THỐNG DASHBOARD (DASHBOARD REGRESSION CHECK)

### 5.1. Tính toàn vẹn của Cơ sở dữ liệu và Tệp cấu hình
Đã đối soát SHA256 và kích thước tệp:
- **`DashBoardD/backend/opsmonitor.db`**:
  - Kích thước: **27,009,024 bytes** (Không đổi).
  - SHA256: `b7d3dc4018aa6f0e...` (Nguyên vẹn 100%).
- **`DashBoardD/backend/app/admin_config.json`**:
  - Kích thước: **189 bytes** (Không đổi).
  - SHA256: `466cd4bcc92f77fd...` (Nguyên vẹn 100%).

### 5.2. Hồi quy Tuyến đường và Xác thực Admin
- Tuyến đường cũ: `#/dashboard`, `#/fpt-shop`, `#/long-chau`, `#/vaccine`, `#/analytics`, `#/employees` đều được bảo toàn.
- Tuyến đường `#/departments` đã được chuyển hướng an toàn sang `#/employees` (Phase 6C.1).
- Tuyến tương thích ngược: `#/test/*` tự động chuyển hướng sang `#/admin/*`.
- Cơ chế xác thực Admin (JWT + TOTP + In-memory Session Hash) và Logout giữ nguyên cấu trúc bảo mật.
- Kết quả chạy toàn bộ 37 bài kiểm tra backend: **37 / 37 PASS (100%)**.

---

## 6. DANH MỤC TRẠNG THÁI NGHIỆM THU CHI TIẾT

| Hạng mục kiểm tra | Phân loại | Ghi chú & Nguyên nhân |
| :--- | :---: | :--- |
| **Kiểm tra trạng thái cổng 8000, 18020, 5174** | **PASS** | Đã xác minh chính xác runtime bằng `Get-NetTCPConnection` và `urllib`. Cả 3 cổng hiện đang tắt. |
| **Kiểm tra mã nguồn & bảo mật Reverse Proxy** | **PASS** | Đã kiểm toán chi tiết: tước `Authorization`, map prefix `/api/test`, xử lý 503 sạch, timeout 300s. |
| **Bộ kiểm thử tự động Backend (Pytest)** | **PASS** | 37 / 37 bài kiểm tra đạt 100%. |
| **Biên dịch Frontend Production (Build)** | **PASS** | Vite build thành công không có lỗi. |
| **Kiểm toán tính toàn vẹn Database & Config** | **PASS** | `opsmonitor.db` và `admin_config.json` không bị thay đổi. |
| **Gọi HTTP trực tiếp tới Port 8000 (Live GET)** | **BLOCKED** | Do DashBoardD Backend hiện đang tắt theo quy tắc an toàn. |
| **Gọi HTTP trực tiếp tới Port 18020 (Live GET)** | **BLOCKED** | Do Test Engine Backend hiện đang tắt theo quy tắc an toàn. |
| **Kiểm tra giao diện trực tiếp trên trình duyệt mở** | **BLOCKED** | Do máy chủ web chưa được bật. |
| **Tác vụ nghiệp vụ có side-effect (POST/PUT/Quét)** | **BLOCKED** | Tuân thủ nghiêm ngặt quy tắc an toàn không chạy side-effect. |

---

## 7. KẾT LUẬN NGHIỆM THU VÀ BƯỚC TIẾP THEO

### 7.1. Đánh giá chung
1. Toàn bộ mã nguồn, logic định tuyến Reverse Proxy, khả năng chịu lỗi và các cải tiến giao diện (File picker, Warehouse status, Retry optimization) đã sẵn sàng 100% về mặt code và build artifacts.
2. Hệ thống hiện ở trạng thái an toàn tuyệt đối, cơ sở dữ liệu và cấu hình không bị xâm phạm.
3. Các bài kiểm tra runtime trực tiếp qua mạng đang ở trạng thái **BLOCKED** vì các tiến trình backend chưa được bật (tuân thủ nguyên tắc không tự ý khởi chạy ngầm).

### 7.2. Yêu cầu phê duyệt từ Người vận hành (Operator Approval Required)
Để hoàn tất bước chuyển từ **BLOCKED** sang **PASS** cho các bài kiểm tra runtime trực tiếp, đề nghị người dùng phê duyệt:
- **Phương án khởi chạy:** Chạy lệnh `start_all.cmd` (hoặc khởi động có kiểm soát DashBoardD backend trên cổng 8000 và Test backend trên cổng 18020).
- Sau khi có phê duyệt, hệ thống sẽ tiến hành gửi các request `GET` chỉ đọc đã được phê duyệt (`/api/health`, `/health`, `/api/test/api/camera/warehouse/status`, ...) để thu thập bằng chứng phản hồi trực tiếp (Live Runtime Proofs).
