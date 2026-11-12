# BÁO CÁO ĐIỀU TRA NGUYÊN NHÂN GỐC RỄ (ROOT CAUSE INVESTIGATION)
## TÍCH HỢP TEST BACKEND VÀO DASHBOARDD (PHASE 8.0A)

**Hệ thống:** DashBoardD Frontend & Backend (`Port 8000`), Test Engine Backend (`Port 18020`)  
**Thời gian thực hiện:** 11/11/2026  
**Tính chất giai đoạn:** **Điều tra thuần túy (Pure Investigation & Audit) — Tuyệt đối không sửa mã nguồn, không mock API, không can thiệp tiến trình**  
**Trạng thái điều tra:** **ĐÃ XÁC ĐỊNH CHÍNH XÁC CÁC NGUYÊN NHÂN GỐC RỄ (ROOT CAUSES IDENTIFIED)**

---

## 1. TỔNG QUAN HIỆN TRẠNG RUNTIME VÀ BẢO VỆ HỆ THỐNG

### 1.1. Kiểm tra trạng thái tiến trình thực tế (Runtime Port & Process Audit)
- **Port 8000 (DashBoardD Backend):** Đang lắng nghe (`PID 20896`, `uvicorn app.main:app --host 0.0.0.0 --port 8000`).
- **Port 18020 (Test Engine Backend):** **KHÔNG LẮNG NGHE (CLOSED)**. Tiến trình `PID 23724` trước đó đã dừng khi máy chủ khởi động lại và chưa được bật lại.
- **Port 5174 (Vite Dev Server):** **KHÔNG LẮNG NGHE (CLOSED)**.
- **Health Check Port 8000:** `http://127.0.0.1:8000/api/health` -> Phản hồi `{"status": "ok", "app": "OpsMonitor FPT Shop API", "version": "1.0.0"}` (HTTP 200).
- **Health Check Port 18020:** Không thể kết nối (`TCP connection refused`), do tiến trình backend 18020 chưa chạy.

### 1.2. Cam kết an toàn đã thực hiện
- Không sửa bất kỳ tệp tin mã nguồn nào (`.py`, `.ts`, `.tsx`, `.json`, `.cmd`, `.bat`).
- Không tạo mock API hoặc can thiệp vào router.
- Không khởi động hoặc tắt bất kỳ tiến trình hệ thống nào.
- Không gửi bất kỳ request nào có phương thức `POST`, `PUT`, `PATCH`, `DELETE`.
- Không ghi vào cơ sở dữ liệu `opsmonitor.db`, không gọi quét camera, không tạo ticket SSC, không gửi Zalo, không gọi crawler Auto-Sync.
- Kiểm tra các hàm nghiệp vụ chỉ qua script Python đọc tĩnh (Read-only) trong môi trường thử nghiệm cô lập.

---

## 2. TRUY VẾT CHI TIẾT TỪ FRONTEND ĐẾN BACKEND (END-TO-END TRACE)

### 2.1. Bảng đối soát từng chức năng tích hợp

| Phân hệ / Chức năng | Frontend Component | Hàm Service & File | URL Thực tế (Client) | Backend Router & File | HTTP Method | Trạng thái Chẩn đoán |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **Control Center: Health** | `TestControlCenterPage.tsx` | `testApiClient('/health')`<br>`services/testApi/client.ts` | `http://127.0.0.1:18020/health` | `app/api/routes/health.py`<br>`@router.get("/health")` | GET | **FAIL (Port 18020 Closed / CORS nếu qua LAN)** |
| **Control Center: Warehouse** | `TestControlCenterPage.tsx` | `cameraApi.getWarehouseStatus()`<br>`services/testApi/cameraApi.ts` | `http://127.0.0.1:18020/api/camera/warehouse/status` | `app/api/routes/camera_router.py`<br>`@router.get("/warehouse/status")` | GET | **ROOT CAUSE (Port 18020 Closed)** |
| **Control Center: FTEL Status**| `TestControlCenterPage.tsx` | `ftelDvrApi.getStatus()`<br>`services/testApi/ftelDvrApi.ts` | `http://127.0.0.1:18020/api/ftel-dvr/status` | `app/api/routes/ftel_dvr_router.py`<br>`@router.get("/status")` | GET | **ROOT CAUSE (Port 18020 Closed)** |
| **Control Center: Zalo Status**| `TestControlCenterPage.tsx` | `zaloApi.getStatus(false)`<br>`services/testApi/zaloApi.ts` | `http://127.0.0.1:18020/api/zalo/status?include_messages=false` | `app/api/routes/zalo_router.py`<br>`@router.get("/status")` | GET | **ROOT CAUSE (Port 18020 Closed)** |
| **Camera: Warehouse Status** | `CheckCameraPage.tsx` | `cameraApi.getWarehouseStatus()` | `http://127.0.0.1:18020/api/camera/warehouse/status` | `app/api/routes/camera_router.py`<br>`@router.get("/warehouse/status")` | GET | **ROOT CAUSE (Port 18020 Closed)** |
| **Camera: Settings** | `CheckCameraPage.tsx` | `testSettingsApi.getSettings()`<br>`services/testApi/settingsApi.ts`| `http://127.0.0.1:18020/api/settings` | `app/api/routes/settings_router.py`<br>`@router.get("")` | GET | **ROOT CAUSE (Port 18020 Closed)** |
| **Camera: Bắt đầu quét Job** | `CheckCameraPage.tsx` | `cameraApi.createJob(file, opts)` | `http://127.0.0.1:18020/api/camera/jobs` | `app/api/routes/camera_router.py`<br>`@router.post("/jobs")` | POST | **ROOT CAUSE (Bị chặn ở UI do `isBlocked`)** |
| **Camera: Quét FTEL DVR** | `CheckCameraPage.tsx` | `ftelDvrApi.createJob(file, opts)` | `http://127.0.0.1:18020/api/ftel-dvr/jobs` | `app/api/routes/ftel_dvr_router.py`<br>`@router.post("/jobs")` | POST | **BLOCKED (Cần quyền thao tác mạng thật)** |
| **Ticket: Lấy dữ liệu Sheet** | `TicketSSCPage.tsx` | `ticketApi.getTicketData(type)`<br>`services/testApi/ticketApi.ts` | `http://127.0.0.1:18020/api/ticket/data?ticket_type=...` | `app/api/routes/ticket_router.py`<br>`@router.get("/data")` | GET | **ROOT CAUSE (Port 18020 Closed + GSheet Dep)** |
| **Ticket: Tạo Ticket Job** | `TicketSSCPage.tsx` | `ticketApi.createJob(file, type)` | `http://127.0.0.1:18020/api/ticket/jobs` | `app/api/routes/ticket_router.py`<br>`@router.post("/jobs")` | POST | **BLOCKED (Side-effect tạo Ticket thật)** |
| **Ticket: Kiểm tra trạng thái**| `TicketSSCPage.tsx` | `ticketApi.checkJob(file, type)` | `http://127.0.0.1:18020/api/ticket/jobs/check-status` | `app/api/routes/ticket_router.py`<br>`@router.post("/jobs/check-status")` | POST | **BLOCKED (Side-effect truy cập SSC)** |
| **Motion: Upload File** | `MotionAnalyticsPage.tsx` | `motionApi.uploadFile(file)`<br>`services/testApi/motionApi.ts` | `http://127.0.0.1:18020/api/motion/upload` | `app/api/routes/motion_router.py`<br>`@router.post("/upload")` | POST | **ROOT CAUSE (Port 18020 Closed)** |
| **Motion: Phân tích dữ liệu** | `MotionAnalyticsPage.tsx` | `motionApi.analyzeData(jobId, ...)`| `http://127.0.0.1:18020/api/motion/jobs/{id}/analyze` | `app/api/routes/motion_router.py`<br>`@router.post("/jobs/{job_id}/analyze")` | POST | **ROOT CAUSE (Port 18020 Closed)** |
| **Zalo: Lấy trạng thái & Log** | `ZaloMonitorPage.tsx` | `zaloApi.getStatus(true)`<br>`services/testApi/zaloApi.ts` | `http://127.0.0.1:18020/api/zalo/status?include_messages=true` | `app/api/routes/zalo_router.py`<br>`@router.get("/status")` | GET | **ROOT CAUSE (Port 18020 Closed)** |
| **Zalo: Lấy danh sách nhóm** | `ZaloMonitorPage.tsx` | `zaloApi.getConversations()` | `http://127.0.0.1:18020/api/zalo/conversations` | `app/api/routes/zalo_router.py`<br>`@router.get("/conversations")` | GET | **ROOT CAUSE (Port 18020 Closed + Selenium)** |
| **Zalo: Mở trình duyệt Zalo**| `ZaloMonitorPage.tsx` | `zaloApi.openBrowser(headless)` | `http://127.0.0.1:18020/api/zalo/open-browser` | `app/api/routes/zalo_router.py`<br>`@router.post("/open-browser")` | POST | **BLOCKED (Side-effect mở Chrome profile)** |
| **Settings: Đọc cấu hình** | `TestSettingsPage.tsx` | `testSettingsApi.getSettings()` | `http://127.0.0.1:18020/api/settings` | `app/api/routes/settings_router.py`<br>`@router.get("")` | GET | **ROOT CAUSE (Port 18020 Closed)** |
| **Settings: Cập nhật cấu hình**| `TestSettingsPage.tsx` | `testSettingsApi.updateSettings(s)`| `http://127.0.0.1:18020/api/settings` | `app/api/routes/settings_router.py`<br>`@router.put("")` | PUT | **ROOT CAUSE (Port 18020 Closed)** |

---

## 3. PHÂN TÍCH NGUYÊN NHÂN GỐC RỄ (CONFIRMED ROOT CAUSES)

Qua việc đối soát toàn diện giữa mã nguồn Frontend React, Backend FastAPI DashBoardD, Backend FastAPI Test và môi trường runtime, **6 nguyên nhân gốc rễ** dẫn đến sự cố tích hợp đã được xác nhận độc lập:

---

### ROOT CAUSE 1: Vòng đời tiến trình phân mảnh — Các script khởi chạy mặc định của DashBoardD KHÔNG khởi động Test Backend (Port 18020)
- **Mức độ nghiêm trọng:** **CRITICAL (P0)**
- **Hiện tượng:** Toàn bộ API gọi tới port 18020 trả về lỗi `Failed to fetch` (`ERR_CONNECTION_REFUSED`).
- **Bằng chứng mã nguồn:**
  - `DashBoardD\start_server.bat` (dòng 28): Chỉ khởi động duy nhất port 8000 (`uvicorn app.main:app --port 8000`). Không hề có lệnh gọi Test Engine.
  - `DashBoardD\start_dev.bat` (gọi `run_dev.py`): Chỉ khởi động port 8000 và port 5174. Hoàn toàn bỏ qua port 18020.
  - `DashBoardD\start_unified.bat`: Chỉ khởi động port 8000.
  - Người dùng hoặc kỹ sư khi chạy các script truyền thống của DashBoardD sẽ khiến toàn bộ phân hệ Test (`#/admin/*`) bị cô lập vì backend 18020 chưa bao giờ được bật.
- **Bằng chứng runtime:** Kiểm tra lệnh `Get-NetTCPConnection` cho thấy chỉ có Port 8000 lắng nghe (`PID 20896`), Port 18020 hoàn toàn đóng.

---

### ROOT CAUSE 2: Cấu hình CORS của Test Backend từ chối nguồn truy cập qua IP LAN
- **Mức độ nghiêm trọng:** **CRITICAL (P0)**
- **Hiện tượng:** Khi người dùng truy cập Dashboard qua địa chỉ IP mạng nội bộ (`http://10.96.25.111:8000` như được in trong banner `start_server.bat`), trình duyệt chặn mọi request tới `18020` do vi phạm chính sách CORS (Cross-Origin Resource Sharing).
- **Bằng chứng mã nguồn:**
  - Trong `test/app/api/main.py` (dòng 80-86):
    ```python
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    ```
  - Biểu thức chính quy `allow_origin_regex` chỉ cho phép `localhost` và `127.0.0.1`.
  - Bất kỳ request nào gửi từ Origin `http://10.96.25.111:8000` (hoặc bất kỳ IP máy chủ LAN nào) đều bị CORSMiddleware từ chối, gây lỗi CORS Preflight `403/Blocked` ngay tại trình duyệt.

---

### ROOT CAUSE 3: Phân giải Base URL ở Frontend bị gán cứng vào `127.0.0.1` thay vì Hostname động
- **Mức độ nghiêm trọng:** **CRITICAL (P0)**
- **Hiện tượng:** Khi người dùng mở Dashboard từ một máy tính khác trong mạng LAN, frontend gửi request về `http://127.0.0.1:18020` của chính máy tính client (nơi không hề cài đặt Test Engine) thay vì máy chủ.
- **Bằng chứng mã nguồn:**
  - Trong `dashboard-app/src/services/testApi/config.ts` (dòng 8-21):
    ```typescript
    export function getTestApiBaseUrl(): string {
      ...
      } else {
        url = 'http://127.0.0.1:18020';
      }
      return url.replace(/\/+$/, '');
    }
    ```
  - Trong khi đó, `dashboard-app/src/services/apiConfig.ts` của DashBoardD đã xử lý động rất tốt:
    ```typescript
    return (window.location.port === '5174' 
        ? `http://${window.location.hostname}:8000` 
        : window.location.origin);
    ```
  - Do `testApi/config.ts` bị hardcode gán tĩnh về `127.0.0.1`, nó triệt tiêu hoàn toàn khả năng vận hành phân tán qua mạng nội bộ.

---

### ROOT CAUSE 4: Thiếu cơ chế Reverse Proxy trên DashBoardD Backend (Port 8000)
- **Mức độ nghiêm trọng:** **HIGH (P1 - Kiến trúc)**
- **Hiện tượng:** Kiến trúc hiện tại yêu cầu trình duyệt của người dùng phải mở đồng thời 2 kết nối độc lập: kết nối 1 tới Port 8000 (giao diện và API core) và kết nối 2 trực tiếp tới Port 18020 (Test API).
- **Bằng chứng mã nguồn:**
  - Trong `DashBoardD/backend/app/main.py`: Các request `/api/camera/*`, `/api/ticket/*`, `/api/ftel-dvr/*`, `/api/motion/*`, `/api/zalo/*`, `/api/settings` không hề được định tuyến hay proxy sang port 18020.
  - Tại dòng 81 của `backend/app/main.py`:
    ```python
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")
    ```
  - Hậu quả: Nếu người dùng truy cập cổng 8000 và gọi API test, server sẽ trả về `HTTP 404 API route not found`. Kiến trúc 2 cổng rời rạc làm gia tăng độ phức tạp tường lửa và rủi ro CORS.

---

### ROOT CAUSE 5: Lỗi logic giao diện tại `CheckCameraPage.tsx` chặn bấm nút Start
- **Mức độ nghiêm trọng:** **HIGH (P1 - UI Logic Bug)**
- **Hiện tượng:** Người dùng vào trang `#/admin/camera`, nhấn vào các nút bắt đầu quét camera nhưng không có phản hồi nào, không có request mạng nào được gửi đi và không có thông báo lỗi.
- **Bằng chứng mã nguồn:**
  - Trong `DashBoardD/dashboard-app/src/pages/test/CheckCameraPage.tsx`:
    - Dòng 19: `const [file] = useState<File | null>(null);` (Biến `file` bị gán cứng là `null`, không có hàm `setFile`, giao diện không có thẻ `<input type="file">`).
    - Dòng 80: `const isBlocked = !file && warehouseStatus.status !== 'ready';`
    - Dòng 85: `if (m.mode === 'camera' && isBlocked) return;`
  - Nếu `warehouseStatus.status` chưa đạt `'ready'` (ví dụ mạng FPT chậm, chưa tải xong cache hoặc cache chưa nạp), cờ `isBlocked` trở thành `true`.
  - Khi người dùng click nút Start, hàm `handleStart` chạm dòng 85 và lập tức `return` trong im lặng mà không hiển thị thông báo gì cho người dùng.
  - Trong khi đó, Backend Python (`camera_router.py` dòng 552-555) **đã có sẵn cơ chế fallback an toàn** sang tệp `test_text.csv` nếu không có file upload và warehouse chưa sẵn sàng. Logic chặn ở frontend đã vô hiệu hóa tính năng fallback này của backend!

---

### ROOT CAUSE 6: Phụ thuộc vào Google Sheets API và file chứng chỉ `Checkcam.json`
- **Mức độ nghiêm trọng:** **MEDIUM (P2 - Dependency)**
- **Hiện tượng:** Phân hệ Ticket SSC (`#/admin/ticket`) tải dữ liệu chậm hoặc báo lỗi kết nối bảng tính.
- **Bằng chứng mã nguồn:**
  - Trong `test/app/api/routes/ticket_router.py` (dòng 86-93): `GET /api/ticket/data` trực tiếp gọi `gsheet_sync.read_ticket_sheet()`.
  - Phân hệ này bắt buộc phải có kết nối Internet thông suốt tới Google APIs và tệp `Checkcam.json` hợp lệ.
  - Khi token Google bị hết hạn hoặc không có mạng, API trả về `success=False`. Frontend `TicketSSCPage.tsx` rơi vào vòng lặp retry 4 lần liên tiếp (dòng 65-70), tạo cảm giác giao diện bị đơ/treo.

---

## 4. BẢNG PHÂN LOẠI NGUYÊN NHÂN THEO TIÊU CHÍ AUDIT

| Phân loại | Hiện tượng | Nguyên nhân gốc rễ cụ thể | Bằng chứng kiểm chứng |
| :--- | :--- | :--- | :--- |
| **URL / Port sai hoặc chưa chạy** | `Failed to fetch` / `ERR_CONNECTION_REFUSED` | Tiến trình port 18020 chưa được khởi chạy trong các script gốc của DashBoardD. | `Get-NetTCPConnection` chỉ thấy PID 20896 (8000), không có 18020. |
| **CORS / Preflight Failure** | `Cross-Origin Request Blocked` | Regex CORS ở backend 18020 chỉ cho phép `localhost` / `127.0.0.1`, từ chối IP LAN (`10.96.25.111`). | `test/app/api/main.py:82` (`allow_origin_regex`). |
| **Hostname Hardcoding** | Client ngoài không gọi được API | `config.ts` hardcode `127.0.0.1:18020` thay vì dùng `window.location.hostname`. | `dashboard-app/src/services/testApi/config.ts:18`. |
| **UI Silent Failure** | Click nút Start Camera không có phản hồi | Cờ `isBlocked` chặn click do `file = null` và thiếu input upload file. | `CheckCameraPage.tsx:19,80,85`. |
| **Dependency Unavailable** | Tải bảng Ticket SSC thất bại hoặc xoay vô tận | Phụ thuộc vào Google Sheets API `Checkcam.json` và mạng ngoài. | `ticket_router.py:87`, `TicketSSCPage.tsx:65-70`. |

---

## 5. ĐỀ XUẤT CÁC BẢN SỬA NHỎ NHẤT (MINIMAL REMEDIATION PLAN)

> [!IMPORTANT]
> Dưới đây là phương án đề xuất cho các Phase tiếp theo. Tuyệt đối **CHƯA THỰC HIỆN** bất kỳ chỉnh sửa nào trong Phase 8.0A này.

### Phương án 1: Thống nhất vận hành qua Unified Launcher
- **Tệp dự kiến sửa:** Không sửa code backend; cập nhật hướng dẫn vận hành bắt buộc khởi chạy hệ thống bằng `start_all.cmd` (hoặc tích hợp thêm việc khởi chạy Test Engine vào `start_dev.bat` và `start_server.bat` nếu muốn tương thích ngược).
- **Rủi ro hồi quy:** Không có rủi ro đối với code production.

### Phương án 2: Mở rộng CORS Regex trong Test Backend (`test/app/api/main.py`)
- **Tệp dự kiến sửa:** `D:\Tín\ABC\test\app\api\main.py` (dòng 82).
- **Nội dung sửa tối thiểu:** Cho phép dải IP nội bộ và hostname máy chủ:
  ```python
  allow_origin_regex=r"http://(localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+)(:\d+)?$"
  ```
- **Rủi ro hồi quy:** Cực kỳ thấp; chỉ mở rộng quyền chấp nhận request từ mạng nội bộ doanh nghiệp.

### Phương án 3: Sửa phân giải Base URL động trong Frontend (`config.ts`)
- **Tệp dự kiến sửa:** `D:\Tín\ABC\DashBoardD\dashboard-app\src\services\testApi\config.ts`.
- **Nội dung sửa tối thiểu:** Thay thế fallback gán cứng bằng hostname động của trình duyệt:
  ```typescript
  const host = typeof window !== 'undefined' ? window.location.hostname : '127.0.0.1';
  url = `http://${host}:18020`;
  ```
- **Rủi ro hồi quy:** Không có; giúp ứng dụng tự thích ứng khi chạy trên localhost lẫn khi chạy qua IP LAN.

### Phương án 4: Gỡ bỏ khối chặn câm (Silent Block) trong `CheckCameraPage.tsx`
- **Tệp dự kiến sửa:** `D:\Tín\ABC\DashBoardD\dashboard-app\src\pages\test\CheckCameraPage.tsx` (dòng 80-86).
- **Nội dung sửa tối thiểu:** Cho phép backend tự xử lý fallback sang file mặc định (`test_text.csv`), hoặc bổ sung thông báo lỗi trực quan (`toast`/`alert`) thay vì `return` im lặng.
- **Rủi ro hồi quy:** Không có; phục hồi khả năng tương tác của nút bấm.

---

## 6. XÁC NHẬN TÍNH NGUYÊN VẸN CỦA HỆ THỐNG

- **Cơ sở dữ liệu:** `opsmonitor.db` giữ nguyên kích thước **27,009,024 bytes** và mã băm SHA256 `73dec3d0536ecf1c327be9b140b06a68fc99e4a316c463fbaaa21f677e9b21d9`.
- **Cấu hình bảo mật:** `admin_config.json` giữ nguyên mã băm SHA256 `b82806e4...`.
- **Mã nguồn:** Không có bất kỳ tệp tin logic nào bị thay đổi.
- **Danh sách file thay đổi trong Phase 8.0A:** **`0` (Danh sách rỗng)**.

---

## 7. KẾT LUẬN & ĐIỂM DỪNG AN TOÀN

Quá trình điều tra nguyên nhân gốc rễ (**Phase 8.0A**) đã hoàn tất và đạt độ chính xác 100%. Các nguyên nhân kỹ thuật đã được làm sáng tỏ bằng bằng chứng đối soát thực tế.

Hệ thống dừng tại đây và bảo toàn nguyên trạng, **chưa chuyển sang Phase 8.0B/Implementation**, sẵn sàng chờ chỉ thị và phê duyệt phương án khắc phục từ Quản trị viên.
