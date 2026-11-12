# TÀI LIỆU BÀN GIAO KỸ THUẬT (TECHNICAL HANDOVER)
**Dự án:** Tích hợp DashBoardD & Module Test Engine  
**Phiên bản:** 1.0 (Phase 7.3 Final Handover)  
**Ngày lập:** 11/11/2026  
**Người bàn giao:** Đội ngũ Kỹ thuật Tích hợp  
**Người tiếp nhận:** Đội ngũ Phát triển & Vận hành Hệ thống

---

## 1. CẤU TRÚC DỰ ÁN & VỊ TRÍ CÁC PHÂN HỆ

Hệ sinh thái dự án đặt tại thư mục gốc `D:\Tín\ABC\`:

```text
D:\Tín\ABC\
├── start_all.cmd                    # Entry point hợp nhất (1-Click Launcher cho Windows)
├── unified_launcher.py              # Script điều phối Python Core (Port checks, Health gates, Process isolation)
│
├── DashBoardD\                      # Phân hệ Dashboard Giám sát & Quản trị Hệ thống
│   ├── backend\                     # FastAPI Backend (Port 8000)
│   │   ├── app\
│   │   │   ├── main.py              # Entry point FastAPI, mount static dist, routers API
│   │   │   ├── core\
│   │   │   │   ├── auth.py          # Cơ chế xác thực JWT, hash SHA256/PBKDF2, Bearer header check
│   │   │   │   ├── config.py        # Settings hệ thống
│   │   │   │   └── database.py      # SQLAlchemy engine kết nối opsmonitor.db
│   │   │   ├── api\                 # Các router: admin.py, auto_sync.py, inside.py, ...
│   │   │   └── admin_config.json    # Cấu hình bảo mật Admin (Hash password, Salt, TOTP secret)
│   │   ├── opsmonitor.db            # Cơ sở dữ liệu SQLite sản xuất (27,009,024 bytes)
│   │   └── tests\                   # 34 bài kiểm thử unit tests (tests/unit, test_admin_auth.py, ...)
│   │
│   ├── dashboard-app\               # React + TypeScript + Vite SPA Frontend
│   │   ├── src\
│   │   │   ├── App.tsx              # Router định tuyến chính (HashRouter)
│   │   │   ├── components\          # Layout, Sidebar (Quản trị & Test), UI controls
│   │   │   ├── pages\
│   │   │   │   ├── Admin.tsx        # Trang điều khiển trung tâm (#/admin)
│   │   │   │   ├── test\            # Các module test: CameraTest, TicketTest, MotionTest, ZaloTest, ...
│   │   │   │   └── SystemAdmin.tsx  # Trang quản trị cũ (#/admin/system, TOTP 2FA, Auto-Sync, Logs)
│   │   │   └── services\
│   │   │       ├── apiConfig.ts     # Cấu hình base URL DashBoardD (Port 8000)
│   │   │       ├── testApi\         # Client kết nối Test Engine (Port 18020)
│   │   │       └── autoSyncApi.ts   # Client API quản trị đồng bộ
│   │   └── dist\                    # Thư mục build tĩnh phục vụ Production
│   │
│   ├── start_dev.bat                # Script chạy độc lập DashBoardD dev (8000 + 5174)
│   ├── start_server.bat             # Script chạy độc lập DashBoardD production server (8000)
│   ├── start_unified.bat            # Script chạy độc lập DashBoardD unified server (8000 reload)
│   └── docs\                        # Thư mục tài liệu kỹ thuật & báo cáo các Phase
│
└── test\                            # Phân hệ Test Engine & Tự động hóa
    ├── app\
    │   └── api\
    │       ├── main.py              # Entry point FastAPI Test Engine (Port 18020)
    │       └── routes\              # Router: health, camera, dvr, motion, ticket, zalo, settings
    ├── desktop\                     # Ứng dụng Desktop Electron độc lập
    ├── run.cmd                      # Script chạy độc lập Electron Dev Test Engine
    ├── scratch\                     # Các script kiểm thử cô lập (verify_launcher_logic.py, ...)
    └── docs\                        # Bản sao đồng bộ tài liệu hệ thống
```

---

## 2. DANH MỤC CÁC ENTRY POINT THỰC TẾ

| Thành phần | Entry Point tệp tin | Lệnh thực thi thực tế từ source | Cổng & Giao thức |
| :--- | :--- | :--- | :---: |
| **Unified Launcher (CMD)** | `D:\Tín\ABC\start_all.cmd` | `start_all.cmd [--dev / --prod / --status]` | Console / Batch |
| **Unified Launcher (Core)**| `D:\Tín\ABC\unified_launcher.py` | `py -3.12 unified_launcher.py` | Python 3.12 |
| **DashBoardD Backend** | `DashBoardD\backend\app\main.py` | `py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --port 8000` | Port 8000 (HTTP) |
| **Test Engine Backend** | `test\app\api\main.py` | `py -3.12 -m uvicorn app.api.main:app --host 127.0.0.1 --port 18020 --no-access-log` | Port 18020 (HTTP) |
| **Vite Dev Server** | `DashBoardD\dashboard-app\` | `npm run dev` | Port 5174 (HTTP) |
| **Production SPA Serving** | `DashBoardD\backend\app\main.py` | Mount thư mục `dashboard-app/dist` trên route `/{full_path:path}` | Port 8000 (HTTP) |
| **Test Desktop Electron** | `test\desktop\` | `npm run electron:dev` (qua `test\run.cmd`) | GUI Desktop |

---

## 3. MỐI QUAN HỆ PHỤ THUỘC GIỮA CÁC DỊCH VỤ (SERVICE DEPENDENCY GRAPH)

```
                            ┌─────────────────────────────────┐
                            │    Trình duyệt Người dùng       │
                            │   (Browser: http://...:8000)    │
                            └────────────────┬────────────────┘
                                             │
                                             ▼
                 ┌────────────────────────────────────────────────────────┐
                 │          DashBoardD Web & API Server (Port 8000)        │
                 │          FastAPI App + Static Mount (dist)             │
                 └──────────────┬──────────────────────────┬──────────────┘
                                │                          │
          [Tất cả route UI chung & DashBoard API]   [Redirect / Tích hợp UI]
                                │                          │
                                ▼                          ▼
                 ┌───────────────────────────┐   ┌────────────────────────┐
                 │ - Trang Dashboard Chính   │   │ - Quản trị Test Center │
                 │ - Giám sát & Báo cáo      │   │   (#/admin)            │
                 │ - Quản trị Hệ thống cũ    │   │ - Camera, Ticket, Zalo,│
                 │   (#/admin/system)        │   │   Motion, Settings     │
                 │ - Xác thực TOTP 2FA & JWT │   └───────────┬────────────┘
                 │ - SQLite: opsmonitor.db   │               │
                 └───────────────────────────┘               │ [HTTP Client Gọi API]
                                                             │ (fetch / axios trực tiếp)
                                                             ▼
                                                 ┌────────────────────────┐
                                                 │   Test Engine Backend  │
                                                 │       (Port 18020)     │
                                                 │  FastAPI (test/app)    │
                                                 └────────────────────────┘
```

### Đặc tính phụ thuộc & Cách ly:
- **Cách ly lỗi (Fault Isolation):** Nếu Test Engine Backend (18020) bị tắt hoặc gặp sự cố, DashBoardD (8000) và toàn bộ các trang giám sát, dashboard, quản trị hệ thống cũ vẫn hoạt động bình thường 100%. Trên giao diện Test Control Center chỉ hiển thị trạng thái `Disconnected` đối với phân hệ test mà không làm crash ứng dụng.
- **Xác thực độc lập:** DashBoardD bảo vệ các API quản trị bằng JWT Bearer Token (TTL 15 phút, lưu trong `sessionStorage`/`localStorage`). Test Engine cung cấp API kiểm thử nội bộ trên `127.0.0.1:18020`.

---

## 4. ĐƯỜNG DẪN CẤU HÌNH, DỮ LIỆU & NHẬT KÝ (CONFIG & DATA PATHS)

| Mục | Đường dẫn tuyệt đối trên ổ đĩa | Mục đích & Lưu ý bảo mật |
| :--- | :--- | :--- |
| **Cơ sở dữ liệu chính** | `D:\Tín\ABC\DashBoardD\backend\opsmonitor.db` | CSDL SQLite (27,009,024 bytes). Lưu trữ dữ liệu vận hành. **Bảo toàn tuyệt đối**. |
| **Cấu hình Quản trị & 2FA** | `D:\Tín\ABC\DashBoardD\backend\app\admin_config.json` | Chứa mật khẩu băm và TOTP Secret. Không commit lộ mã nguồn. |
| **Bản build Frontend** | `D:\Tín\ABC\DashBoardD\dashboard-app\dist\` | File tĩnh đã tối ưu hóa cho Production serving. |
| **Môi trường Vite (nếu có)**| `D:\Tín\ABC\DashBoardD\dashboard-app\.env` | Cấu hình biến `VITE_API_URL` và `VITE_TEST_API_URL`. |
| **Thư mục Test Scratches** | `D:\Tín\ABC\test\scratch\` | Chứa các script kiểm thử tự động hóa nội bộ (verify logic, regression). |
| **Tài liệu nghiệm thu Phase**| `D:\Tín\ABC\DashBoardD\docs\` và `test\docs\` | Lưu trữ toàn bộ tài liệu kiến trúc từ Phase 5 đến Phase 7. |

---

## 5. CÁC LỆNH KIỂM TRA AN TOÀN & GIÁM SÁT HỆ THỐNG (AUDIT COMMANDS)

Kỹ sư vận hành có thể sử dụng các lệnh sau để kiểm tra hệ sinh thái mà **không gây tác dụng phụ**:

```powershell
# 1. Kiểm tra trạng thái toàn bộ dịch vụ qua Unified Launcher:
D:\Tín\ABC\start_all.cmd --status

# 2. Kiểm tra các port đang mở trên máy chủ:
Get-NetTCPConnection -LocalPort 8000, 18020, 5174 -State Listen | Select-Object LocalPort, OwningProcess

# 3. Kiểm tra tính sẵn sàng của Health Endpoint:
curl.exe -s http://127.0.0.1:8000/api/health
# Mong đợi: {"status":"ok",...}

curl.exe -s http://127.0.0.1:18020/health
# Mong đợi: {"status":"healthy","service":"test-python-backend",...}

curl.exe -s -I http://localhost:8000/
# Mong đợi: HTTP/1.1 200 OK (phục vụ index.html)

# 4. Kiểm tra tính toàn vẹn cơ sở dữ liệu:
(Get-Item "D:\Tín\ABC\DashBoardD\backend\opsmonitor.db").Length
# Mong đợi: 27009024

(Get-FileHash "D:\Tín\ABC\DashBoardD\backend\opsmonitor.db").Hash
# Mong đợi: 73DEC3D0536ECF1C327BE9B140B06A68FC99E4A316C463FBAAA21F677E9B21D9

# 5. Chạy bộ kiểm thử tự động của DashBoardD Backend:
cd D:\Tín\ABC\DashBoardD\backend
py -3.12 -m pytest tests -q
# Mong đợi: 34 passed (100%)

# 6. Chạy bộ kiểm thử tự động của Unified Launcher:
py -3.12 D:\Tín\ABC\test\scratch\verify_phase_7_2_scenarios.py
# Mong đợi: ALL 9 OPERATIONAL READINESS & RECOVERY SCENARIOS PASSED (100%)
```

---

## 6. NHỮNG GIỚI HẠN KỸ THUẬT & VÙNG CHƯA XÁC MINH (KNOWN BOUNDARIES)

1. **Ranh giới Network LAN vs Localhost:**
   - Test Engine Backend (`18020`) được cấu hình bind tại `127.0.0.1` theo thiết kế bảo mật để tránh rò rỉ API kiểm thử ra ngoài mạng nội bộ. Trình duyệt client chạy trên cùng máy tính (hoặc qua port-forwarding) sẽ gọi trực tiếp được. Nếu client truy cập từ máy tính khác trong mạng LAN (`http://10.96.25.111:8000`), client đó cần được định tuyến hoặc Test Engine cần bind `0.0.0.0` nếu muốn cho phép máy ngoài điều khiển test.
2. **Quyền hạn Windows Taskkill:**
   - Lệnh dọn dẹp `taskkill /F /T /PID` của launcher chỉ có quyền kết thúc các tiến trình cùng mức đặc quyền người dùng (User-level). Nếu một service chạy dưới quyền `SYSTEM` hoặc `Administrator`, người dùng cần chạy console với quyền `Administrator` tương ứng để quản lý.
3. **Nghiệp vụ phần cứng Camera & Zalo:**
   - Trong toàn bộ quá trình tích hợp từ Phase 5 đến Phase 7, các API có tác dụng phụ (quét dải IP camera thật, gửi tin Zalo, tạo Ticket SSC, crawler Auto-Sync) **chỉ được kiểm toán tĩnh ở cấp độ mã nguồn** để đảm bảo an toàn tuyệt đối cho thiết bị và dữ liệu sản xuất. Khi đưa vào vận hành thực địa, cần kiểm thử từng bước với tài khoản sandbox / mạng lab thử nghiệm.

---

## 7. XÁC NHẬN BÀN GIAO & TÍNH NGUYÊN VẸN

- **Mã nguồn Production:** Bảo toàn 100%, không bị sửa đổi ngoài phạm vi các bản vá bảo mật đã duyệt ở Phase 6C.
- **Cơ sở dữ liệu:** Không bị ghi đè, không bị mất mát bản ghi.
- **Bộ công cụ khởi chạy:** Hoạt động ổn định, có tài liệu hướng dẫn đầy đủ, có cơ chế an toàn No-Kill và Rollback tức thì.
- **Tài liệu:** Đã đồng bộ đầy đủ giữa `DashBoardD/docs` và `test/docs`.
