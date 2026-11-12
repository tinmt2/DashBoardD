---
title: DashBoardD & Test Engine Monorepo
emoji: 📊
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 8000
---

# DashBoardD & Test Engine Monorepo

Hệ thống quản lý, giám sát và vận hành hợp nhất:
1. **DashBoardD (Core System):** Giám sát và quản lý báo cáo vi phạm, đối soát nợ cho FPT Shop, Long Châu và Vaccine.
2. **Test Application Engine:** Nghiệp vụ kiểm tra Camera RTSP / Hikvision DVR, Ticket SSC, Zalo Monitor AI và đồng bộ dữ liệu.

---

## 1. KIẾN TRÚC VÀ CẤU TRÚC THƯ MỤC

Hệ thống được tổ chức theo mô hình **Monorepo** với hai tiến trình backend FastAPI độc lập, giao tiếp thông qua Reverse Proxy:

```text
DashBoardD/
├── backend/                       # Dashboard FastAPI Backend (Port 8000)
│   ├── app/
│   │   ├── api/                   # API routes (fpt_shop, long_chau, vaccine, admin, test_proxy)
│   │   ├── core/                  # Cấu hình bảo mật, JWT, TOTP 2FA
│   │   ├── services/              # Nghiệp vụ crawler, báo cáo, session
│   │   ├── admin_config.json      # [LOCAL-ONLY, GITIGNORED] Cấu hình bảo mật local
│   │   └── admin_config.example.json # File mẫu cấu hình an toàn
│   ├── tests/                     # 37 unit tests kiểm thử Dashboard
│   └── opsmonitor.db              # [LOCAL-ONLY, GITIGNORED] SQLite database chính
├── dashboard-app/                 # Dashboard Frontend (React + TypeScript + Vite + Tailwind)
│   ├── src/
│   │   ├── pages/                 # Các trang Dashboard và nhánh test (`pages/test/`)
│   │   ├── services/              # API clients (`autoSyncApi`, `insideApi`, `testApi`)
│   │   └── context/               # TestTaskContext quản lý trạng thái tác vụ
│   ├── dist/                      # Bản build HTML/JS tĩnh phục vụ production
│   └── package.json
├── test_engine/                   # Test Engine FastAPI Backend (Port 18020)
│   ├── app/
│   │   ├── api/                   # Routes (camera, ftel_dvr, ticket, zalo, settings, ...)
│   │   ├── services/              # Hikvision DVR, Ticket Crawler, Zalo AI, GSheets sync
│   │   ├── config.py & paths.py   # Đường dẫn động và cấu hình
│   │   └── ...
│   ├── desktop/                   # Mã nguồn Electron Desktop client (rebuild khi cần)
│   ├── scripts/                   # Script dev và build backend standalone
│   ├── tests/                     # 28 tests (unit, api, golden, integration)
│   ├── runtime/                   # [LOCAL-ONLY, GITIGNORED] zalo_monitor.db, browser profile
│   ├── config.json                # [LOCAL-ONLY, GITIGNORED] Cấu hình Test Engine
│   ├── config.example.json        # File mẫu cấu hình Test Engine an toàn
│   ├── Checkcam.json              # [LOCAL-ONLY, GITIGNORED] Service account Google Sheets
│   └── chromedriver.exe           # [LOCAL-ONLY, GITIGNORED] WebDriver cho Zalo Selenium
├── docs/                          # Toàn bộ tài liệu kỹ thuật, runbook và báo cáo Phase 9
├── unified_launcher.py            # Trình quản lý khởi chạy hợp nhất đa chế độ
├── start_all.cmd                  # Shortcut khởi chạy bằng click chuột trên Windows
└── .gitignore                     # Bộ quy tắc bảo vệ dữ liệu nhạy cảm nghiêm ngặt
```

---

## 2. YÊU CẦU MÔI TRƯỜNG & CÀI ĐẶT

### 2.1. Yêu cầu hệ thống
- **Hệ điều hành:** Windows 10 / 11 / Windows Server 2019+
- **Python:** Python 3.12.x (`py -3.12 --version`)
- **Node.js:** Node.js v18+ và npm 9+ (`node -v`, `npm -v`)
- **Google Chrome:** Cài đặt Chrome bản mới nhất (cho tính năng Zalo Monitor Selenium)

### 2.2. Cài đặt Dependencies

#### Dashboard Backend:
```bash
cd backend
py -3.12 -m pip install -r requirements.txt
```

#### Test Engine Backend:
```bash
cd test_engine
py -3.12 -m pip install -r requirements.txt
```

#### Dashboard Frontend:
```bash
cd dashboard-app
npm install
```

---

## 3. THIẾT LẬP CẤU HÌNH LOCAL (TỪ FILE MẪU)

Hệ thống tuân thủ nghiêm ngặt nguyên tắc **No Secrets in Git**. Các file cấu hình chứa thông tin thật không được đưa vào Git tracking. Trước khi chạy lần đầu, hãy chuẩn bị các file cấu hình local:

1. **Cấu hình Quản trị Dashboard:**
   - Sao chép `backend/app/admin_config.example.json` thành `backend/app/admin_config.json`.
   - Cập nhật mật khẩu băm, salt và TOTP secret theo quy định quản trị.
2. **Cấu hình Test Engine:**
   - Sao chép `test_engine/config.example.json` thành `test_engine/config.json`.
   - Điền Google Sheets ID, Zalo Secret và thông số cần thiết nếu sử dụng các tính năng liên quan.
3. **Google Service Account Credentials (nếu dùng Google Sheets sync):**
   - Đặt file `Checkcam.json` hợp lệ vào thư mục `test_engine/`.

---

## 4. HƯỚNG DẪN KHỞI CHẠY

### 4.1. Khởi chạy bằng Unified Launcher (Khuyến nghị)

Tại thư mục gốc `DashBoardD/`, nhấp đúp vào `start_all.cmd` (hoặc chạy từ console `python unified_launcher.py`).

Menu tương tác:
```text
=================================================================
   UNIFIED LAUNCHER - DASHBOARDD & TEST APPLICATION
=================================================================
 [1] Khởi chạy Chế độ Phát triển (Dev Mode: Port 5174, 8000, 18020)
 [2] Khởi chạy Chế độ Vận hành (Production Mode: Port 8000, 18020)
 [3] Kiểm tra trạng thái hệ thống (Read-only Status & Health Check)
 [0] Thoát
=================================================================
```

Hoặc sử dụng cờ dòng lệnh (CLI flags):
```cmd
# Chế độ Dev (Frontend HMR + 2 Backends)
start_all.cmd --dev

# Chế độ Production (FastAPI 8000 serve static dist + Test Engine 18020)
start_all.cmd --prod

# Kiểm tra trạng thái hệ thống (Read-only non-destructive)
start_all.cmd --status
```

### 4.2. Khởi chạy Từng Thành Phần Độc Lập

Khi cần debug chuyên sâu hoặc kiểm thử riêng biệt từng phân hệ:

#### 1. Chạy độc lập Dashboard Backend (Port 8000):
```cmd
cd backend
py -3.12 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### 2. Chạy độc lập Test Engine Backend (Port 18020):
```cmd
cd test_engine
py -3.12 -m uvicorn app.api.main:app --host 127.0.0.1 --port 18020 --no-access-log
```

#### 3. Chạy độc lập Dashboard Frontend (Port 5174):
```cmd
cd dashboard-app
npm run dev
```

---

## 5. CỔNG MẠNG, HEALTH ENDPOINTS & REVERSE PROXY

| Thành phần | Cổng | Giao thức | URL Kiểm tra Sức khỏe | Chuỗi mong đợi | Mục đích chính |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **Dashboard Backend** | `8000` | HTTP GET | `http://127.0.0.1:8000/api/health` | `{"status":"ok"}` | Core API & Production Static Web UI |
| **Test Engine Backend** | `18020` | HTTP GET | `http://127.0.0.1:18020/health` | `"test-python-backend"` | Engine Camera, DVR, Ticket, Zalo |
| **Reverse Proxy** | `8000` | HTTP GET | `http://127.0.0.1:8000/api/test/health` | `"test-python-backend"` | Forward `/api/test/*` sang `127.0.0.1:18020` |
| **Frontend Dev Server** | `5174` | HTTP GET | `http://localhost:5174` | HTML `<html` | Vite React Dev Server với HMR |

### Cơ chế Reverse Proxy & Fail-safe:
- Dashboard Backend chứa reverse proxy tại `backend/app/api/test_proxy.py`.
- Mọi request từ giao diện người dùng gửi tới `/api/test/{path}` sẽ được chuyển tiếp trong suốt sang `http://127.0.0.1:18020/{path}`.
- Khi Test Engine không chạy hoặc gặp sự cố, proxy trả về ngay mã `HTTP 503 Service Unavailable` kèm thông báo tiếng Việt rõ ràng, giúp Dashboard Frontend hiển thị banner cảnh báo và **không làm crash Dashboard Backend**.

---

## 6. QUY TẮC DỪNG TIẾN TRÌNH & XỬ LÝ XUNG ĐỘT CỔNG (NO-KILL PRINCIPLE)

- **Dừng an toàn:** Nhấn `Ctrl + C` tại cửa sổ Launcher. Launcher chỉ dừng đúng các tiến trình do nó sinh ra (`SPAWNED_PROCESSES`), không tắt các tiến trình có sẵn từ trước.
- **Nguyên tắc No-Kill:** Launcher tuyệt đối không tự ý tắt (`taskkill`) bất kỳ tiến trình lạ nào đang chiếm dụng cổng 8000 hoặc 18020.
- **Xử lý xung đột cổng:**
  ```powershell
  # Kiểm tra PID đang chiếm cổng
  Get-NetTCPConnection -LocalPort 8000, 18020 -State Listen | Select-Object LocalPort, OwningProcess
  
  # Xác định tên ứng dụng
  Get-Process -Id <PID> | Select-Object Id, ProcessName, Path
  ```

---

## 7. CẢNH BÁO TÁC VỤ CÓ TÁC DỤNG PHỤ (SIDE-EFFECT WARNINGS)

> [!WARNING]
> CÁC TÍNH NĂNG DƯỚI ĐÂY TÁC ĐỘNG TRỰC TIẾP TỚI THIẾT BỊ PHẦN CỨNG MẠNG VÀ HỆ THỐNG SẢN XUẤT THẬT. BẮT BUỘC PHẢI CÓ SỰ PHÊ DUYỆT TRƯỚC KHI THỰC HIỆN:
> 
> 1. **Quét Camera IP RTSP / Hikvision DVR:** Phát sinh lưu lượng gói tin lớn quét toàn dải mạng camera nội bộ.
> 2. **Tạo Ticket SSC:** Gửi request tạo ticket hỗ trợ thật trên cổng SSC của doanh nghiệp.
> 3. **Gửi tin nhắn Zalo:** Gửi tin nhắn Zalo thật tới tài khoản khách hàng / nhân viên.
> 4. **Ghi Google Sheets Sản xuất:** Ghi đè hoặc thêm dòng vào trang tính quản trị chính thức.
> 
> *Trong toàn bộ quá trình audit và kiểm thử Phase 1 đến Phase 5, các tính năng trên đều được đặt ở chế độ `NOT TESTED BY DESIGN` để đảm bảo an toàn tuyệt đối.*

---

## 8. TÀI LIỆU KỸ THUẬT BỔ SUNG

Các tài liệu kỹ thuật chi tiết được lưu trữ trong thư mục `docs/`:
- [Sổ tay Vận hành Hệ thống](docs/OPERATIONS_RUNBOOK.md)
- [Báo cáo Kiểm kê & Kế hoạch Hợp nhất (Phase 9.0)](docs/PHASE_9_0_CONSOLIDATION_AUDIT_REPORT.md)
- [Báo cáo Sao lưu & An ninh (Phase 9.1)](docs/PHASE_9_1_BACKUP_SECURITY_REPORT.md)
- [Kế hoạch Kỹ thuật Chi tiết (Phase 9.2)](docs/PHASE_9_2_PRE_MIGRATION_PLAN.md)
- [Báo cáo Di chuyển Mã nguồn (Phase 9.3)](docs/PHASE_9_3_CONTROLLED_MIGRATION_REPORT.md)
- [Báo cáo Kiểm thử Hồi quy (Phase 9.4)](docs/PHASE_9_4_REGRESSION_REPORT.md)
- [Báo cáo Tổng kết & Bàn giao (Phase 9.5)](docs/PHASE_9_5_FINAL_REVIEW.md)
