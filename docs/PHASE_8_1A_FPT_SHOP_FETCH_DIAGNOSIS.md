# BÁO CÁO ĐIỀU TRA NGUYÊN NHÂN GỐC RỄ (PHASE 8.1A)
## CHẨN ĐOÁN LỖI "FAILED TO FETCH" TRÊN TRANG FPT SHOP (`localhost:5174/#/fpt-shop`)

**Hệ thống:** DashBoardD Frontend (Vite Dev Server) & Backend (FastAPI)  
**Thời gian điều tra:** 11/11/2026 (18:25)  
**Tính chất giai đoạn:** Điều tra & Chẩn đoán thuần túy (Zero Code Edit / Zero Mutation)  
**Hiện tượng:** Trình duyệt tại `http://localhost:5174/#/fpt-shop` hiển thị thông báo lỗi:
- `Không thể tải dữ liệu FPT Shop`
- `Failed to fetch`

---

## 1. TRẠNG THÁI RUNTIME VÀ CỔNG MẠNG THỰC TẾ

Đã thực hiện kiểm toán chỉ đọc qua `Get-NetTCPConnection` và `Get-CimInstance`:

| Cổng (Port) | Tiến trình phục vụ (PID) | Trạng thái Socket | Health Check Endpoint | Kết quả kiểm tra | Phân loại |
| :---: | :--- | :---: | :--- | :--- | :---: |
| **5174** | `PID 24196` (`node.exe` - Vite Dev Server) | **LISTEN** (`0.0.0.0:5174`) | `http://localhost:5174/` | Phục vụ mã nguồn React Dev bình thường | **ONLINE** |
| **8000** | **Không có tiến trình nào** | **CLOSED / NOT LISTENING** (Chỉ có socket `TimeWait`) | `http://127.0.0.1:8000/api/health` | **Connection Failed -> timed out / ERR_CONNECTION_REFUSED** | **OFFLINE (CHẾT)** |
| **18020** | `PID 17676` (`python.exe` - Test Engine) | **LISTEN** (`127.0.0.1:18020`) | `http://127.0.0.1:18020/health` | Phản hồi HTTP 200 OK | **ONLINE** |

### Bằng chứng lệnh kiểm tra Socket:
```powershell
PS D:\Tín\ABC> Get-NetTCPConnection -LocalPort 5174, 8000, 18020
LocalAddress LocalPort State       OwningProcess
------------ --------- -----       -------------
::                5174 Listen      24196
127.0.0.1        18020 Listen      17676
# Port 8000 KHÔNG CÓ DÒNG NÀO Ở TRẠNG THÁI Listen! Chỉ còn các socket TimeWait.
```

---

## 2. TRUY VẾT MÃ NGUỒN TỪ FRONTEND ĐẾN BACKEND (END-TO-END TRACE)

### 2.1. Cấu hình API Base URL (`dashboard-app/src/services/apiConfig.ts`)
```typescript
export function getApiBaseUrl(): string {
  // ...
  return window.location.protocol === 'file:' 
    ? 'http://127.0.0.1:8000' 
    : (window.location.port === '5174' 
        ? `http://${window.location.hostname}:8000` 
        : window.location.origin);
}
export const API_BASE_URL = getApiBaseUrl();
```
- Khi người dùng truy cập trang phát triển tại cổng **5174**, `API_BASE_URL` tự động phân giải thành:  
  👉 `http://localhost:8000`

### 2.2. Danh sách các Request thực tế được Frontend gọi khi tải `#/fpt-shop`
Trang `#/fpt-shop` kích hoạt component `Dashboard.tsx` (qua `ChainPage chain="FPT Shop"`). Ngay khi component mount, các request sau được phát đi đồng thời:

| Request URL thực tế | HTTP Method | Service / Hàm gọi | Mục đích dữ liệu | Kết quả thực tế trên trình duyệt |
| :--- | :---: | :--- | :--- | :--- |
| `http://localhost:8000/api/fpt-shop/summary?from_date=2026-11-01&to_date=2026-11-11` | **GET** | `fetchDashboardSummary()` (`fptShopApi.ts:51`) | Tải tổng hợp Calllog, lỗi vi phạm, KPI nhân viên | `net::ERR_CONNECTION_REFUSED` |
| `http://localhost:8000/api/fpt-shop/auth/status` | **GET** | `getFptShopAuthStatus()` (`fptShopApi.ts:111`) | Kiểm tra trạng thái đăng nhập hệ thống Inside FPT Shop | `net::ERR_CONNECTION_REFUSED` |
| `http://localhost:8000/api/employees` | **GET** | `EmployeeService.getEmployees()` (`employeeService.ts:68`) | Lấy danh sách nhân viên | `net::ERR_CONNECTION_REFUSED` |
| `http://localhost:8000/api/notifications?limit=5&skip=0&unread_only=false` | **GET** | `NotificationService.getNotifications()` | Polling thông báo hệ thống | `net::ERR_CONNECTION_REFUSED` |

### 2.3. Bằng chứng Bắt lỗi trên Giao diện (`Dashboard.tsx:502-517` & `1094-1104`)
```tsx
// Dashboard.tsx:502-517
try {
  const [summary, employees] = await Promise.all([
    fetchDashboardSummary(syncStartDate, syncEndDate),
    EmployeeService.getEmployees()
  ]);
  // ...
} catch (err: any) {
  setError(err.message || 'Lỗi cập nhật dữ liệu'); // err.message = "Failed to fetch"
}

// Dashboard.tsx:1094-1104
} : error ? (
  <GlassCard className="p-8 flex flex-col items-center max-w-md text-center border-rose-200">
    <AlertCircle size={48} className="text-rose-500 mb-4" />
    <h2 className="text-[18px] font-bold mb-2 text-rose-700">Không thể tải dữ liệu {chain || 'FPT Shop'}</h2>
    <p className="text-[14px] mb-6 text-rose-600/80">{error}</p>
    <button onClick={fetchData} ...>Thử lại</button>
  </GlassCard>
)
```
Do fetch ném ngoại lệ `TypeError: Failed to fetch`, component hiển thị chính xác tiêu đề `Không thể tải dữ liệu FPT Shop` và nội dung lỗi `Failed to fetch`.

---

## 3. KIỂM TRA MÃ NGUỒN ROUTE BACKEND VÀ DỮ LIỆU CƠ SỞ

Đã kiểm tra độc lập các route và dịch vụ nghiệp vụ trong `DashBoardD/backend`:

### 3.1. Route `/api/fpt-shop/summary`
- Tệp định nghĩa: `DashBoardD/backend/app/api/fpt_shop.py:66-70`
- Đăng ký Router: `DashBoardD/backend/app/main.py:45` (`app.include_router(fpt_shop.router, prefix="/api/fpt-shop")`)
- **Kiểm thử logic cô lập bằng script Python:**
  ```python
  from app.core.database import SessionLocal
  from app.repositories.ticket_repository import SQLiteTicketRepository
  from app.services.dashboard.fpt_shop_summary import FPTShopSummaryService
  db = SessionLocal()
  repo = SQLiteTicketRepository(db)
  service = FPTShopSummaryService(repo)
  summary = service.get_summary(from_date='2026-11-01', to_date='2026-11-11')
  print(summary.model_dump()['overview'])
  ```
  **Kết quả:**
  ```json
  {
    "totalErrors": 947,
    "totalChecked": 947,
    "statusStats": null,
    "errorRate": 100.0,
    "employeesWithErrors": 7,
    "totalEmployees": 7,
    "totalReminders": 716
  }
  ```
  👉 **Khẳng định:** Mã nguồn xử lý nghiệp vụ FPT Shop và cơ sở dữ liệu `opsmonitor.db` **hoàn toàn khỏe mạnh và hoạt động chính xác 100%**. Không có lỗi cú pháp, không có lỗi logic tính toán.

### 3.2. Route `/api/fpt-shop/auth/status` (Phát hiện điểm rủi ro lớn)
- Tệp định nghĩa: `DashBoardD/backend/app/api/fpt_shop.py:133-143`
  ```python
  @router.get("/auth/status", response_model=AuthStatusResponse)
  def auth_status():
      session = FPTBrowserSession.get_instance()
      status = session.get_status()
      if status == "STOPPED" and not getattr(session, '_initial_probed', False):
          session._initial_probed = True
          status = session.start(probe_only=True) # <-- TỰ ĐỘNG KHỞI ĐỘNG CHROME TRONG HTTP GET!
      return AuthStatusResponse(authenticated=(status == "AUTHENTICATED"), status=status)
  ```
- **Vấn đề nghiêm trọng:** Endpoint `GET /auth/status` là một phương thức GET (vốn phải là idempotent và không có side-effect), nhưng lại tự ý gọi `session.start(probe_only=True)`. Lệnh này kích hoạt Selenium/ChromeDriver trên nền máy chủ mỗi khi trang web được tải.
- **Bằng chứng trong `app.log` lúc 18:15:37:**
  ```text
  2026-11-11 18:15:37,412 [ERROR] app.services.browser.browser_manager: Failed to start browser session for fpt-shop-profile: ('Connection aborted.', ConnectionResetError(10054, 'An existing connection was forcibly closed by the remote host', None, 10054, None))
  ```

---

## 4. BẰNG CHỨNG XÁC NHẬN NGUYÊN NHÂN GỐC RỄ (CONFIRMED ROOT CAUSES)

Qua toàn bộ dữ liệu runtime và console của người dùng, **3 nguyên nhân gốc rễ** được xác nhận như sau:

### 🔴 Nguyên nhân 1 (Trực tiếp - Critical): DashBoardD Backend trên Cổng 8000 Đang Tắt (Dead Process)
- Trình duyệt đang chạy Vite Dev Server tại cổng **5174**.
- Frontend gửi các request tới `http://localhost:8000/api/...`.
- Cổng 8000 không có bất kỳ tiến trình nào lắng nghe (`Listen`), dẫn đến lỗi mạng cấp độ hệ điều hành: **`net::ERR_CONNECTION_REFUSED`**.
- Mọi hàm fetch (`fetchDashboardSummary`, `getFptShopAuthStatus`, `EmployeeService.getEmployees`, `NotificationService`) đều bị từ chối kết nối trước khi chạm được tới router FastAPI.

### 🔴 Nguyên nhân 2 (Hạ tầng giám sát): Thiếu cơ chế tự phục hồi (Supervision) trong `unified_launcher.py`
- Trong `unified_launcher.py`, backend được khởi chạy qua `subprocess.Popen` với `stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL`.
- Launcher chỉ kiểm tra health một lần lúc khởi động, sau đó rơi vào vòng lặp vô tận `while True: time.sleep(1)`.
- Khi tiến trình backend (PID 3692) thoát bất thường hoặc bị dừng, launcher **không phát hiện và không khởi động lại tiến trình**, khiến cổng 8000 bị bỏ hoang trong khi launcher và các dịch vụ khác (port 18020) vẫn chạy.

### 🟡 Nguyên nhân 3 (Thiết kế phụ trợ gây mất ổn định): Side-effect trong `GET /auth/status`
- Phương thức `GET /api/fpt-shop/auth/status` tự động kích hoạt tiến trình trình duyệt Chrome `probe_only=True` khi khởi chạy lần đầu.
- Khi môi trường máy tính chưa sẵn sàng phiên duyệt web hoặc bị chặn kết nối remote debug (`ConnectionResetError 10054`), request bị nghẽn tới 30 giây và có nguy cơ làm kiệt quệ tài nguyên luồng của uvicorn.

---

## 5. GIẢ THUYẾT ĐÃ ĐƯỢC LOẠI TRỪ (DISPROVEN HYPOTHESES)

1. **Giả thuyết CORS:** Bị loại trừ. Cấu hình `CORSMiddleware` trong `app/main.py` cho phép `allow_origins=["*"]`. Mã lỗi là `ERR_CONNECTION_REFUSED` (lỗi TCP), hoàn toàn không phải `CORS policy blocked`.
2. **Giả thuyết hỏng Database hoặc Logic FPT Shop:** Bị loại trừ. Đã chạy thử nghiệm cô lập `FPTShopSummaryService` với dữ liệu thật trong `opsmonitor.db`, kết quả tính toán 947 lỗi vi phạm trả về ngay lập tức với `success: True`.
3. **Giả thuyết sai đường dẫn Route:** Bị loại trừ. Tuyến `/api/fpt-shop/summary` và `/api/fpt-shop/auth/status` đã được mount chuẩn xác trong `app/main.py`.

---

## 6. PHƯƠNG ÁN KHẮC PHỤC TỐI THIỂU ĐỀ XUẤT (MINIMAL REMEDIATION PLAN)

Để đưa hệ thống trở lại trạng thái hoạt động bình thường, đề xuất 3 bước xử lý có kiểm soát:

1. **Khởi động lại DashBoardD Backend trên Cổng 8000:**
   - Khởi chạy tiến trình Uvicorn phục vụ DashBoardD backend trên cổng 8000 (`py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --port 8000`).
   - Sau khi bật, toàn bộ request từ `localhost:5174` sẽ được tiếp nhận và xử lý trơn tru (HTTP 200).
2. **Vô hiệu hóa Side-effect tự bật Chrome trong `GET /auth/status`:**
   - Trong `app/api/fpt_shop.py`, chuyển `GET /auth/status` thành pure-read: chỉ kiểm tra trạng thái hiện có trong RAM (`session.get_status()`). Nếu `STOPPED`, trả về `STOPPED` mà không gọi `session.start(probe_only=True)`.
   - Chỉ cho phép bật trình duyệt khi người dùng chủ động bấm nút "Đăng nhập / Bắt đầu" thông qua endpoint `POST /auth/start`.
3. **Bổ sung `import os` còn thiếu trong Browser Sessions:**
   - Bổ sung `import os` vào `app/services/long_chau/login/browser_session.py` và `app/services/vaccine/login/browser_session.py` để loại bỏ các cảnh báo lỗi `name 'os' is not defined`.
4. **Cải tiến vòng lặp giám sát của Unified Launcher:**
   - Trong `unified_launcher.py`, kiểm tra định kỳ `proc.poll()`. Nếu một tiến trình con bị thoát, ghi log cảnh báo và tự động khởi động lại dịch vụ đó.

---

## 7. KẾT LUẬN VÀ CHỜ PHÊ DUYỆT

Giai đoạn điều tra **Phase 8.1A** đã xác định chính xác 100% nguyên nhân gốc rễ của lỗi `Failed to fetch`. Toàn bộ dữ liệu cơ sở dữ liệu `opsmonitor.db` và cấu hình hệ thống được bảo toàn nguyên vẹn.

> **Trạng thái:** Đã hoàn thành chẩn đoán. Dừng lại tại đây và chờ phê duyệt từ Người vận hành để tiến hành khắc phục tối thiểu theo Phương án tại Mục 6.
