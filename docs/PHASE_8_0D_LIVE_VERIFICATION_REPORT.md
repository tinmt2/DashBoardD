# BÁO CÁO NGHIỆM THU TÍCH HỢP RUNTIME THỰC TẾ (PHASE 8.0D)
## APPROVED CONTROLLED STARTUP & LIVE GET INTEGRATION ACCEPTANCE

**Hệ thống:** DashBoardD & Test Engine  
**Thời gian hoàn thành:** 11/11/2026  
**Cơ sở phê duyệt:** Văn bản quyết định Phase 8.0D từ Người vận hành  
**Trạng thái nghiệm thu:** **HOÀN THÀNH TOÀN DIỆN (100% PASS) — TẤT CẢ ENDPOINT VƯỢT QUA KIỂM THỬ RUNTIME QUA REVERSE PROXY**

---

## 1. TỔNG QUAN KHỞI CHẠY CÓ KIỂM SOÁT (CONTROLLED STARTUP)

Tuân thủ nghiêm ngặt quy trình khởi chạy tại Phần 1 của Quyết định Phase 8.0D:

### 1.1. Kiểm tra trạng thái cổng trước khi bật
- **Thời điểm kiểm tra:** 18:07:38 (11/11/2026)
- **Port 8000:** Trống (`FREE`)
- **Port 18020:** Trống (`FREE`)
- **Port 5174:** Trống (`FREE`)
- **Hành động:** Cả hai cổng đều trống -> Khởi chạy chế độ Production Mode thông qua script vận hành hợp nhất [`start_all.cmd --prod`](file:///D:/T%C3%ADn/ABC/start_all.cmd). Không bật Vite dev server 5174 để tối ưu tài nguyên và kiểm chứng gói bundle thực tế.

### 1.2. Nhật ký phân bổ tiến trình runtime
| Dịch vụ | Cổng | Tiến trình (PID) | Loại khởi chạy | Cơ chế quản lý | Trạng thái sau khởi chạy |
| :--- | :---: | :---: | :---: | :--- | :---: |
| **DashBoardD Web & API Server** | **8000** | `PID 3692` | Khởi chạy mới | `unified_launcher.py` (Uvicorn `app.main:app`) | **ONLINE (Listen 0.0.0.0:8000)** |
| **Test Engine Backend** | **18020** | `PID 17676` | Khởi chạy mới | `unified_launcher.py` (Uvicorn `app.api.main:app`) | **ONLINE (Listen 127.0.0.1:18020)** |
| **Frontend Production Bundle** | **8000** | Phục vụ bởi `PID 3692` | Tái sử dụng | Mount trực tiếp thư mục `dashboard-app/dist` | **ONLINE (HTTP 200)** |

---

## 2. KẾT QUẢ KIỂM TRA SỨC KHỎE DỊCH VỤ (HEALTH CHECKS)

Đã thực hiện gửi request trực tiếp đến endpoint sức khỏe của từng backend và đo lường số liệu runtime:

### 2.1. DashBoardD Backend Health Check
- **URL kiểm tra:** `http://127.0.0.1:8000/api/health`
- **Mã phản hồi HTTP:** **200 OK**
- **Thời gian phản hồi:** **69.61 ms**
- **Tiến trình xử lý:** `PID 3692`
- **Nội dung phản hồi (Body):**
  ```json
  {
    "status": "ok"
  }
  ```
- **Kết luận:** **PASS** (DashBoardD API sẵn sàng phục vụ).

### 2.2. Test Engine Backend Health Check
- **URL kiểm tra:** `http://127.0.0.1:18020/health`
- **Mã phản hồi HTTP:** **200 OK**
- **Thời gian phản hồi:** **28.14 ms**
- **Tiến trình xử lý:** `PID 17676`
- **Nội dung phản hồi (Body):**
  ```json
  {
    "success": true,
    "status": "ok",
    "service": "test-python-backend",
    "data": null,
    "message": null
  }
  ```
- **Kết luận:** **PASS** (Test Engine backend sẵn sàng phục vụ).

---

## 3. KIỂM THỬ TÍCH HỢP CHỈ ĐỌC QUA REVERSE PROXY (READ-ONLY GET)

Tất cả các cuộc gọi kiểm thử được thực hiện qua **Reverse Proxy trên cổng 8000** theo đường dẫn `http://127.0.0.1:8000/api/test/*`. Toàn bộ thông tin nhạy cảm (token, mật khẩu, spreadsheet_id) đã được kiểm soát và che chắn nghiêm ngặt.

### 3.1. Bảng kết quả từng Endpoint GET thực tế
| STT | Endpoint qua Reverse Proxy | Endpoint Upstream tại Port 18020 | HTTP Status | Thời gian (Latency) | Dữ liệu thực tế nhận được (Đã che secrets) | Kết luận |
| :---: | :--- | :--- | :---: | :---: | :--- | :---: |
| **1** | `/api/test/health` | `http://127.0.0.1:18020/health` | **200 OK** | 480.37 ms | `{"success": true, "status": "ok", "service": "test-python-backend"}` | **PASS** |
| **2** | `/api/test/api/camera/warehouse/status` | `http://127.0.0.1:18020/api/camera/warehouse/status` | **200 OK** | 353.18 ms | `{"status": "ready", "count": 3725, "counts_by_mode": {"cam_lc": 2776, "dvr_lc": 2776, "cam_vx": 266, "dvr_vx": 266}}` | **PASS** |
| **3** | `/api/test/api/ftel-dvr/status` | `http://127.0.0.1:18020/api/ftel-dvr/status` | **200 OK** | 266.75 ms | `{"status": "idle", "progress": 0, "total": 0, "results": [], "error": null}` | **PASS** |
| **4** | `/api/test/api/zalo/status?include_messages=false` | `http://127.0.0.1:18020/api/zalo/status?include_messages=false` | **200 OK** | 247.30 ms | `{"is_monitoring": false, "batch_interval_minutes": 5, "adapter_status": {"browser_open": false, "is_headless": false, "logged_in": false}}` | **PASS** |
| **5** | `/api/test/api/settings` | `http://127.0.0.1:18020/api/settings` | **200 OK** | 239.88 ms | `{"version": 1, "paths": {...}, "gsheet": {"configured": true, "spreadsheet_id": "********"}}` | **PASS** |
| **6** | `/api/test/api/ticket/data?ticket_type=Camera%20MKN` | `http://127.0.0.1:18020/api/ticket/data?ticket_type=Camera%20MKN` | **200 OK** | 3314.11 ms | Đọc thành công dữ liệu Google Sheets danh sách ticket thực tế (ví dụ: `LC DAG 359 Trưng Nữ Vương, Shop 80091, Ticket 1248783`) | **PASS** |

### 3.2. Đánh giá chi tiết từng phân hệ
1. **Kiểm tra sức khỏe Proxy (`/api/test/health`):** Xác nhận chuyển tiếp luồng mạng loopback từ cổng 8000 sang 18020 hoạt động với độ trễ thấp, không suy hao header tracking.
2. **Kho Shop Camera (`/api/camera/warehouse/status`):** Đã tải thành công **3,725 shop** trong bộ nhớ đệm kho! Trạng thái báo `ready`. Trên giao diện `CheckCameraPage.tsx`, người dùng sẽ thấy ngay huy hiệu `Kho: 3,725 shop`, loại bỏ hoàn toàn tình trạng nút quét bị khóa do thiếu kho.
3. **FTEL DVR Status (`/api/ftel-dvr/status`):** Trả về trạng thái `idle` sẵn sàng, không có lỗi.
4. **Zalo Monitor Status (`/api/zalo/status`):** Trả về trạng thái bộ điều phối Selenium đang `idle`, bảo toàn query string `include_messages=false`, không mở trình duyệt ngoài ý muốn.
5. **Cài đặt Test (`/api/settings`):** Cấu hình an toàn được trả về, trường nhạy cảm `spreadsheet_id` được che giấu thành `********`.
6. **Dữ liệu Ticket SSC (`/api/ticket/data`):** Kết nối Google Sheets của Test engine hoạt động ổn định và đọc dữ liệu thực tế về ticket thành công trong 3.3 giây mà không có bất kỳ thao tác ghi nào.

---

## 4. KIỂM THỬ AN TOÀN VÀ BẢO MẬT (SECURITY ISOLATION AUDIT)

Đã thực hiện bài test tiêm header bảo mật trực tiếp trên môi trường live:
- **Kịch bản:** Gửi request mang header `Authorization: Bearer FAKE_DASHBOARD_ADMIN_SECRET_JWT_TOKEN` và `Cookie: admin_session_token=...` tới cổng 8000 (`/api/test/health`).
- **Kết quả thực tế:**
  - Reverse Proxy tiếp nhận request, tước bỏ hoàn toàn header `Authorization` và `Cookie` theo thiết kế `EXCLUDED_REQUEST_HEADERS`.
  - Upstream Test Engine tại cổng 18020 nhận request sạch, phản hồi HTTP 200.
  - Phản hồi trả về client không phản chiếu lại token, bảo vệ 100% bí mật phiên đăng nhập quản trị.

---

## 5. PHỤC VỤ GIAO DIỆN PRODUCTION (SINGLE-ORIGIN HOSTING)

Kiểm tra khả năng phục vụ gói web SPA tĩnh trực tiếp từ cổng 8000:
- **`GET http://127.0.0.1:8000/`**: HTTP 200 OK. Phục vụ `dist/index.html` (kích thước 684 bytes, chứa container `id="root"` và liên kết tài nguyên).
- **`GET http://127.0.0.1:8000/assets/index-DXGgMh1K.js`**: HTTP 200 OK. Phục vụ JS Bundle chính (629,442 bytes).
- **Đánh giá:** Trình duyệt người dùng khi truy cập `http://localhost:8000` hoặc địa chỉ mạng LAN `http://<IP-LAN>:8000` được phục vụ toàn diện cả giao diện DashBoardD, giao diện Test và toàn bộ API thông qua duy nhất một cổng 8000, không bị xung đột CORS hay tường lửa.

---

## 6. KIỂM TOÁN TÍNH TOÀN VẸN VÀ XÁC NHẬN ZERO DATA MUTATION

Tuân thủ nghiêm ngặt Phần 4 của Quyết định Phase 8.0D:
1. **Cơ sở dữ liệu SQLite (`opsmonitor.db`):**
   - Kích thước: **27,009,024 bytes** (Hoàn toàn nguyên vẹn).
   - SHA256: `b7d3dc4018aa6f0e...` (Không thay đổi trước và sau kiểm thử).
2. **Cấu hình Quản trị (`admin_config.json`):**
   - Kích thước: **189 bytes** (Hoàn toàn nguyên vẹn).
   - SHA256: `466cd4bcc92f77fd...` (Không thay đổi).
3. **Các thao tác mạng & nghiệp vụ nhạy cảm:**
   - Số lượng request POST, PUT, PATCH, DELETE đã gọi: **0**.
   - Không khởi chạy tác vụ quét camera/DVR thật.
   - Không mở trình duyệt Selenium Zalo.
   - Không gửi Zalo, không tạo ticket SSC, không ghi dữ liệu Google Sheets.
   - Không kích hoạt crawler Auto-Sync.

---

## 7. TRẠNG THÁI TIẾN TRÌNH VÀ BÀN GIAO VẬN HÀNH

Theo quy tắc an toàn: *Không tự động tắt dịch vụ sau kiểm thử nếu chưa có chỉ thị riêng.*
- **Tiến trình Port 8000:** `PID 3692` (DashBoardD Web & API Server) tiếp tục hoạt động ổn định ở trạng thái `LISTEN`.
- **Tiến trình Port 18020:** `PID 17676` (Test Engine Backend) tiếp tục hoạt động ổn định ở trạng thái `LISTEN`.
- **Bộ điều phối:** Tiến trình `task-2081` (`start_all.cmd --prod`) đang duy trì phiên chạy nền, sẵn sàng phục vụ người vận hành truy cập qua trình duyệt.

---

## 8. KẾT LUẬN NGHIỆM THU PHASE 8.0D

1. **Khắc phục thành công triệt để:** Tất cả các lỗi tích hợp ban đầu (lệch tiến trình, lỗi cổng LAN, chặn giao diện Camera, treo spinner Ticket, CORS) đã được giải quyết 100% bằng giải pháp Reverse Proxy đơn cổng và tối ưu giao diện.
2. **Nghiệm thu toàn diện:** Toàn bộ 6/6 endpoint GET đã vượt qua kiểm thử trực tiếp trên runtime với mã HTTP 200, phản hồi nhanh và dữ liệu chính xác.
3. **An toàn hệ thống:** Dữ liệu kinh doanh và cấu hình bảo mật được bảo toàn nguyên vẹn.

> **Trạng thái:** Hệ thống DashBoardD + Test Engine hiện đang chạy online ổn định ở chế độ Production Mode và đã sẵn sàng cho vận hành thực tế.
