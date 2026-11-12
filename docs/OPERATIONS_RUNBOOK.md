# SỔ TAY VẬN HÀNH HỆ THỐNG (OPERATIONS RUNBOOK)
**Dự án:** DashBoardD & Test Application Engine  
**Phiên bản tài liệu:** 1.0 (Phase 7.3 Handover)  
**Ngày phát hành:** 11/11/2026  
**Đối tượng sử dụng:** Quản trị viên hệ thống (Sysadmin), Kỹ sư vận hành (DevOps / SRE), Kỹ sư kiểm thử (QA/QC)

---

## 1. TỔNG QUAN KIẾN TRÚC HỆ THỐNG

Hệ thống tích hợp hợp nhất hai thành phần cốt lõi:
1. **DashBoardD (Core System):**
   - **Frontend:** Single Page Application (SPA) phát triển bằng React + TypeScript + Vite, hỗ trợ HashRouter (`#/admin`, `#/departments`, ...).
   - **Backend:** FastAPI (Python 3.12) phục vụ API giám sát, xác thực quản trị (JWT + TOTP 2FA), lưu trữ dữ liệu tại `opsmonitor.db` (SQLite).
   - **Phục vụ tĩnh (Production):** Backend FastAPI lắng nghe trên port 8000, tự động mount thư mục `dashboard-app/dist` để phục vụ giao diện web mà không cần Nginx/Apache.
2. **Test Engine (Module Kiểm thử & Tự động hóa):**
   - **Backend:** FastAPI (Python 3.12) lắng nghe trên port `18020`, cung cấp API kiểm thử Camera RTSP/DVR, Ticket SSC, Motion Detection, Zalo Notifications và Cài đặt Test.
   - **Frontend:** Được tích hợp trực tiếp vào nhánh `#/admin/*` của DashBoardD frontend (`#/admin/camera`, `#/admin/ticket`, `#/admin/motion`, `#/admin/zalo`, `#/admin/settings`).

---

## 2. ĐIỀU KIỆN MÔI TRƯỜNG CẦN THIẾT (PREREQUISITES)

Trước khi khởi chạy hệ thống, máy chủ / máy trạm Windows cần đảm bảo:

| Yêu cầu | Phiên bản tối thiểu | Lệnh kiểm tra | Ghi chú |
| :--- | :---: | :--- | :--- |
| **Hệ điều hành** | Windows 10 / 11 / Server 2019+ | `cmd /c ver` | Hỗ trợ Command Prompt và PowerShell |
| **Python** | Python 3.12.x | `py -3.12 --version` hoặc `python --version` | Cần cài đặt Uvicorn, FastAPI |
| **Node.js** | Node.js v18+ & npm 9+ | `node -v` và `npm -v` | Bắt buộc cho Dev Mode (`npm run dev`) |
| **Cổng mạng khả dụng** | 8000, 18020, 5174 | `Get-NetTCPConnection -LocalPort 8000,18020,5174` | Phải không bị chiếm dụng bởi app lạ |

---

## 3. HƯỚNG DẪN KHỞI CHẠY BẰNG UNIFIED LAUNCHER

Điểm khởi chạy chính được đặt tại thư mục repository:  
📁 `D:\Tín\ABC\DashBoardD\start_all.cmd`  
*(Đồng thời có wrapper chuyển tiếp tiện lợi tại thư mục gốc: `D:\Tín\ABC\start_all.cmd`)*

### 3.1. Khởi chạy bằng Giao diện Menu Tương tác (Interactive GUI)
Nhấp đúp chuột vào tệp `start_all.cmd`. Cửa sổ console sẽ hiển thị menu:
```text
=================================================================
   UNIFIED LAUNCHER - DASHBOARDD & TEST APPLICATION
=================================================================
 [1] Khởi chạy Chế độ Phát triển (Dev Mode: Port 5174, 8000, 18020)
 [2] Khởi chạy Chế độ Vận hành (Production Mode: Port 8000, 18020)
 [3] Kiểm tra trạng thái hệ thống (Read-only Status & Health Check)
 [0] Thoát
=================================================================
Nhập lựa chọn của bạn [0-3]:
```

### 3.2. Khởi chạy bằng Dòng lệnh (CLI Flags)
Có thể gọi trực tiếp từ PowerShell hoặc CMD:
```cmd
# Khởi chạy Chế độ Phát triển
D:\Tín\ABC\start_all.cmd --dev

# Khởi chạy Chế độ Vận hành
D:\Tín\ABC\start_all.cmd --prod

# Kiểm tra trạng thái hệ thống (Read-only, không bật/tắt tiến trình)
D:\Tín\ABC\start_all.cmd --status

# Xem hướng dẫn trợ giúp
D:\Tín\ABC\start_all.cmd --help
```

---

## 4. CHI TIẾT CÁC CHẾ ĐỘ VẬN HÀNH

### [1] Chế độ Phát triển (Dev Mode)
- **Mục đích:** Dành cho lập trình viên phát triển tính năng, kiểm thử giao diện với tính năng Hot Module Reload (HMR).
- **Các tiến trình được quản lý:**
  1. `DashBoardD Backend`: Chạy trên port `8000` (`http://localhost:8000`).
  2. `Test Engine Backend`: Chạy trên port `18020` (`http://localhost:18020`).
  3. `Vite Frontend Dev Server`: Chạy trên port `5174` (`http://localhost:5174`).
- **Hành vi:** Sau khi cả 3 service vượt qua kiểm tra sức khỏe, launcher sẽ tự động bật trình duyệt mặc định truy cập `http://localhost:5174`.

### [2] Chế độ Vận hành (Production Mode)
- **Mục đích:** Dành cho môi trường nội bộ doanh nghiệp ổn định, tối ưu tài nguyên RAM và CPU.
- **Các tiến trình được quản lý:**
  1. `DashBoardD Web & API Server`: Chạy trên port `8000` (`http://localhost:8000` hoặc `http://10.96.25.111:8000`), tự động phục vụ file tĩnh từ thư mục `dashboard-app/dist`.
  2. `Test Engine Backend`: Chạy trên port `18020`.
- **Cơ chế bảo vệ bản build:** Launcher tự động kiểm tra nếu `dist/index.html` chưa có mới chạy `npm run build`. Nếu bản build đã tồn tại, launcher **không build đè** để tránh làm sai lệch cấu hình sản phẩm.
- **Hành vi:** Tự động mở trình duyệt tại `http://localhost:8000` sau khi health check đạt chuẩn.

### [3] Kiểm tra trạng thái (Status Check)
- **Mục đích:** Kiểm tra nhanh tình trạng hoạt động của toàn bộ dịch vụ trên server mà **không làm thay đổi bất kỳ tiến trình nào** (Read-only audit).
- **Kết quả hiển thị:** Báo rõ từng cổng `[ONLINE]`, `[OFFLINE]`, hoặc `[CẢNH BÁO]` (nếu bị xung đột), kèm trạng thái sẵn sàng của thư mục build `dist`.

### [0] Thoát (Exit)
- Đóng launcher an toàn với mã thoát `0`. Nếu các service đã chạy từ trước, chúng vẫn tiếp tục hoạt động độc lập trên nền.

---

## 5. BẢNG DANH MỤC CỔNG, DỊCH VỤ VÀ HEALTH ENDPOINT

| Dịch vụ | Cổng | Giao thức | URL Kiểm tra Sức khỏe (Health Check) | Chuỗi định danh mong đợi (Snippet) | URL Truy cập Chính |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **DashBoardD Backend** | `8000` | HTTP GET | `http://127.0.0.1:8000/api/health` | `"ok"` | `http://localhost:8000` |
| **Test Engine Backend** | `18020` | HTTP GET | `http://127.0.0.1:18020/health` | `"test-python-backend"` | `http://localhost:18020` |
| **Frontend Dev Server** | `5174` | HTTP GET | `http://localhost:5174` | Thẻ HTML (`<html`) | `http://localhost:5174` |
| **Production Web UI** | `8000` | HTTP GET | `http://localhost:8000/` | Thẻ HTML (`<html`) | `http://localhost:8000/#/admin` |

> [!NOTE]
> Lưu ý quan trọng: Health endpoint của DashBoardD nằm tại `/api/health`, trong khi của Test Engine nằm tại `/health` (không có tiền tố `/api`). Launcher đã được cấu hình chính xác cho từng endpoint tương ứng.

---

## 6. HƯỚNG DẪN XỬ LÝ XUNG ĐỘT CỔNG (`CONFLICT_UNKNOWN`)

### Triệu chứng
Khi khởi chạy, console xuất hiện dòng cảnh báo màu đỏ hoặc dấu chấm than:
```text
[!] CẢNH BÁO: Cổng 8000 đang bị chiếm dụng bởi tiến trình không phải DashBoardD!
    Launcher sẽ KHÔNG kill tiến trình lạ. Vui lòng kiểm tra và giải phóng cổng 8000.
```

### Nguyên nhân kỹ thuật
Cổng `8000`, `18020` hoặc `5174` đang có một tiến trình lạ kết nối (ví dụ: IIS, máy chủ Node độc lập, Skype, hoặc một service khác), và khi gửi HTTP GET tới health endpoint, nội dung trả về không khớp với chữ ký hệ thống.

### Quy trình xử lý (Chuẩn an toàn No-Kill):
1. **Tìm PID chiếm dụng cổng:** Mở PowerShell (Run as Administrator) và chạy:
   ```powershell
   Get-NetTCPConnection -LocalPort 8000, 18020, 5174 -State Listen | Select-Object LocalPort, OwningProcess
   ```
2. **Xác định danh tính tiến trình:**
   ```powershell
   Get-Process -Id <PID_TÌM_ĐƯỢC> | Select-Object Id, ProcessName, Path, Description
   ```
3. **Đánh giá và đóng tiến trình:**
   - Nếu là tiến trình ứng dụng của bên thứ ba: Người dùng tự đánh giá xem có thể tắt ứng dụng đó hoặc chuyển sang cổng khác không.
   - Nếu là tiến trình Python cũ bị treo (Zombie process): Có thể đóng qua Task Manager hoặc lệnh:
     ```powershell
     Stop-Process -Id <PID_TÌM_ĐƯỢC> -Force
     ```
4. **Kiểm tra lại trạng thái:**
   ```cmd
   D:\Tín\ABC\start_all.cmd --status
   ```
   Khi cổng đã chuyển sang `[OFFLINE]`, khởi chạy lại chế độ mong muốn.

---

## 7. HƯỚNG DẪN XỬ LÝ HẾT GIỜ (HEALTH TIMEOUT) & KHỞI ĐỘNG THẤT BẠI

### Triệu chứng
Màn hình dừng ở trạng thái `[Chờ] Đang kiểm tra cổng sẵn sàng... [HẾT GIỜ]` và thông báo hủy quy trình.

### Các bước chẩn đoán và khắc phục:
1. **Kiểm tra môi trường Python:**
   Kiểm tra xem các thư viện backend có bị thiếu sót hay không bằng cách gọi lệnh trực tiếp từ console:
   - Với DashBoardD Backend:
     ```cmd
     cd D:\Tín\ABC\DashBoardD\backend
     py -3.12 -m uvicorn app.main:app --port 8000
     ```
   - Với Test Engine (Monorepo):
     ```cmd
     cd D:\Tín\ABC\DashBoardD\test_engine
     py -3.12 -m uvicorn app.api.main:app --port 18020
     ```
     *(Lưu ý: Thư mục gốc `D:\Tín\ABC\test` vẫn được giữ nguyên vẹn để đối chiếu lịch sử).*
   Quan sát log lỗi hiển thị trực tiếp (ImportError, Database Lock, SyntaxError nếu có).
2. **Kiểm tra khóa SQLite (Database Lock):**
   Nếu tệp `opsmonitor.db` đang bị một tiến trình khác khóa độc quyền (Exclusive Lock), Uvicorn có thể bị nghẽn lúc khởi tạo kết nối SQLAlchemy. Hãy đảm bảo không mở file `.db` bằng các tool SQLite có bật chế độ lock ghi mà chưa commit/rollback.

---

## 8. CÁCH CHẠY TỪNG ỨNG DỤNG ĐỘC LẬP BẰNG SCRIPT CŨ (LEGACY SCRIPTS)

Các script cũ của dự án được bảo toàn nguyên vẹn 100% để phục vụ debug chuyên sâu từng thành phần:

| Thành phần | Script khởi chạy | Thư mục làm việc | Mô tả hoạt động |
| :--- | :--- | :--- | :--- |
| **Test Engine (Electron App)** | `run.cmd` | `D:\Tín\ABC\test\` | Khởi chạy giao diện Electron Desktop độc lập của Test Engine (`npm run electron:dev`). |
| **DashBoardD Fullstack Dev** | `start_dev.bat` | `D:\Tín\ABC\DashBoardD\` | Chạy `run_dev.py` bật đồng thời FastAPI 8000 và Vite 5174 (không kèm Test Engine 18020). |
| **DashBoardD Server Đơn lẻ** | `start_server.bat` | `D:\Tín\ABC\DashBoardD\` | Dọn cổng 8000 và khởi chạy Uvicorn độc lập phục vụ mạng nội bộ (`0.0.0.0:8000`). |
| **DashBoardD 1 Server Unified**| `start_unified.bat` | `D:\Tín\ABC\DashBoardD\` | Kiểm tra build `dist` và chạy Uvicorn port 8000 chế độ reload. |
| **DashBoardD Desktop App** | `open_desktop_app.bat`| `D:\Tín\ABC\DashBoardD\` | Khởi chạy bản xem trước Desktop Electron của Dashboard (`npm run electron:preview`). |

---

## 9. NGUYÊN TẮC SHUTDOWN AN TOÀN & QUYỀN SỞ HỮU TIẾN TRÌNH

Unified Launcher áp dụng nguyên lý phân tách quyền sở hữu tiến trình nghiêm ngặt:
- **Tiến trình do Launcher tạo ra (`SPAWNED_PROCESSES`):**
  - Được lưu danh sách PID cụ thể trong bộ nhớ session.
  - Khi người dùng nhấn `Ctrl + C` hoặc một service gặp lỗi startup, launcher gọi `clean_shutdown()` và chỉ gửi lệnh `taskkill /F /T /PID` cho đúng các PID trong danh sách này.
- **Tiến trình có sẵn từ trước (Pre-existing Processes):**
  - Nếu port 8000 hoặc 18020 đã đang chạy hợp lệ trước khi bật launcher, launcher sẽ **TÁI SỬ DỤNG** dịch vụ đó.
  - Khi đóng launcher hoặc nhấn Ctrl+C, các dịch vụ có sẵn từ trước này **HOÀN TOÀN KHÔNG BỊ TẮT**, đảm bảo tính liên tục cho các dịch vụ đang phục vụ người dùng khác.

---

## 10. DANH MỤC CÁC NGHIỆP VỤ CÓ TÁC DỤNG PHỤ (SIDE-EFFECT WARNINGS)

> [!WARNING]
> CÁC THAO TÁC DƯỚI ĐÂY TÁC ĐỘNG TRỰC TIẾP TỚI MẠNG LƯỚI, HỆ THỐNG PHẦN CỨNG HOẶC DỮ LIỆU THẬT. BẮT BUỘC PHẢI CÓ SỰ PHÊ DUYỆT CỦA QUẢN TRỊ VIÊN TRƯỚC KHI THỰC HIỆN TRÊN MÔI TRƯỜNG THỰC TẾ:

| Nghiệp vụ | Phân hệ | Endpoint / Thao tác | Tác động thực tế | Yêu cầu xác nhận |
| :--- | :---: | :--- | :--- | :---: |
| **Quét luồng Camera RTSP / DVR** | Test Engine (18020) | `#/admin/camera`<br>`/api/camera/scan` | Phát sinh lưu lượng gói tin lớn quét toàn dải IP mạng LAN/VLAN của camera. | Cần thông báo bộ phận IT Network |
| **Tạo Ticket SSC Hỗ trợ** | Test Engine (18020) | `#/admin/ticket`<br>`/api/ticket/create` | Gửi request tạo Ticket thật vào hệ thống quản lý SSC của công ty. | Tuyệt đối không bấm tạo Ticket thật khi kiểm thử |
| **Phân tích chuyển động (Motion)**| Test Engine (18020) | `#/admin/motion`<br>`/api/motion/analyze` | Chiếm dụng CPU/GPU giải mã video luồng thời gian thực. | Giám sát tài nguyên CPU |
| **Gửi thông báo Zalo** | Test Engine (18020) | `#/admin/zalo`<br>`/api/zalo/send` | Gửi tin nhắn Zalo OA / ZNS thật đến số điện thoại người dùng (tốn chi phí và làm phiền khách hàng). | Chỉ thử nghiệm với số điện thoại nội bộ được duyệt |
| **Chạy đồng bộ ngay (Auto-Sync)** | DashBoardD (8000) | `#/admin/system`<br>`/api/auto-sync/run-now` | Gửi crawler tải dữ liệu FPT Shop, Long Châu, Vaccine và ghi đè vào DB. | Chỉ chạy ngoài giờ cao điểm |
| **Ghi Google Sheets** | DashBoardD (8000) | `/api/inside/*` | Ghi dòng log/thống kê vào trang tính Google Drive thật của doanh nghiệp. | Kiểm tra Sheet ID trước khi chạy |

---

## 11. BẢO VỆ DỮ LIỆU, CẤU HÌNH & XÁC THỰC BẢO MẬT

1. **Cơ sở dữ liệu SQLite (`DashBoardD/backend/opsmonitor.db`):**
   - Kích thước hiện tại: `27,009,024 bytes` (SHA256: `73dec3d0...`).
   - Sao lưu định kỳ: Định kỳ copy tệp `.db` sang thư mục sao lưu an toàn khi server không chạy hoặc qua lệnh SQLite Online Backup API.
2. **Tệp cấu hình Quản trị (`DashBoardD/backend/app/admin_config.json`):**
   - Chứa mật khẩu Admin đã băm (PBKDF2/Argon2), muối (salt) và khóa bí mật TOTP.
   - Tuyệt đối không xóa hoặc ghi đè tệp này. Quyền truy cập tệp trên Windows NTFS chỉ nên cấp cho tài khoản chạy dịch vụ.
3. **Cơ chế Token TTL & Đăng xuất:**
   - JWT Token quản trị có thời gian sống (TTL) là **15 phút**.
   - Khi hết hạn hoặc người dùng bấm Đăng xuất (`#/admin/system`), frontend gọi endpoint `/api/admin/logout` để backend đưa token vào danh sách thu hồi (Revocation Blocklist).
   - Tuyệt đối không in Token, Secret hay Mật khẩu ra màn hình console hay tệp nhật ký (logs).

---

## 12. QUY TRÌNH ROLLBACK LAUNCHER VỀ TRẠNG THÁI CŨ

Trong trường hợp cần quay trở lại phương thức vận hành hoàn toàn bằng script cũ trước Phase 7:
1. **Bước 1:** Dừng cửa sổ `start_all.cmd` (nếu đang mở).
2. **Bước 2 (Không rủi ro):** Chỉ cần xóa hai tệp tin mới tạo ở thư mục gốc:
   - `D:\Tín\ABC\start_all.cmd`
   - `D:\Tín\ABC\unified_launcher.py`
3. **Bước 3:** Sử dụng lại các script độc lập:
   - Khởi động backend DashBoardD qua `DashBoardD\start_server.bat`.
   - Khởi động giao diện Test qua `test\run.cmd`.
4. **Kết quả Rollback:** Toàn bộ hệ thống trở về trạng thái nguyên bản 100% trước Phase 7.1 mà không có bất kỳ tổn thất hay thay đổi nào về mã nguồn nghiệp vụ.
