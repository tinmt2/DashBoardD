# BÁO CÁO KIỂM TOÁN VÀ KẾ HOẠCH HỢP NHẤT MÃ NGUỒN
# PHASE 9.0 — SOURCE CODE CONSOLIDATION AUDIT: DASHBOARDD + TEST ENGINE

**Ngày kiểm toán:** 11/11/2026  
**Thực hiện:** AI Pair Programmer / System Auditor  
**Phạm vi kiểm toán:**  
- `D:\Tín\ABC\DashBoardD` (Repository chính hiện có)
- `D:\Tín\ABC\test` (Thư mục mã nguồn Test Engine)
- `D:\Tín\ABC` (Unified Launcher và các script quản lý cấp cao)  
**Mục tiêu:** Kiểm kê toàn diện hiện trạng, đánh giá rủi ro, bảo vệ bí mật/dữ liệu vận hành và lập kế hoạch chi tiết hợp nhất mã nguồn vào một Git repository duy nhất tại `DashBoardD`, bảo toàn 100% chức năng hiện có mà KHÔNG làm gián đoạn hệ thống.

---

## 1. TÓM TẮT HIỆN TRẠNG (EXECUTIVE SUMMARY)

1. **DashBoardD:**
   - **Vai trò:** Hệ thống giám sát vận hành chính (FPT Shop, Long Châu, Dược phẩm/Vaccine, Quản lý Nhân sự, Quản trị hệ thống).
   - **Kiến trúc:** Frontend React + TypeScript + Vite + Tailwind (cổng phát triển 5174, cổng production 8000 qua static file); Backend FastAPI (cổng 8000).
   - **Tình trạng Git:** Đã khởi tạo Git repository (`https://github.com/tinmt2/DashBoardD.git`), nhánh `main`, commit mới nhất `ab13c1d`. Working tree hiện có **18 file đã sửa đổi (modified)** và **31 file/thư mục chưa theo dõi (untracked)** (bao gồm module Test Proxy, giao diện Test và tài liệu tích hợp từ các Phase 6 - 8).
   - **Giao diện Test Engine:** Toàn bộ 6 phân hệ của Test Engine (Check Camera, FTEL DVR, Ticket SSC, Motion Analytics, Zalo Monitor, Cài đặt) đã được chuyển đổi hoàn chỉnh thành React components tại `dashboard-app/src/pages/test/` và tích hợp vào Router/Layout tại `#/admin/*`.

2. **Test Engine (`test`):**
   - **Vai trò:** Backend chuyên biệt xử lý tự động hóa nặng: Quét camera Hikvision, quét đầu ghi FTEL DVR, tự động hóa Ticket SSC qua Selenium, Zalo Live Monitor (quét tin nhắn sự cố & phân tích AI Gemini), đồng bộ Google Sheets.
   - **Kiến trúc:** Backend FastAPI độc lập trên cổng 18020 (`app.api.main:app`). Trước đây có frontend Electron desktop cũ (`desktop/`), hiện đã chuyển giao tính năng sang Web Dashboard.
   - **Tình trạng Git:** **[VERIFIED] KHÔNG có Git repository**. Thư mục `test` không chứa `.git`, không có Git history riêng, không có Git submodules.
   - **Dữ liệu & Rác tích tụ:** Chứa nhiều script sửa lỗi một lần (one-off patches), file rác tạm thời, file xuất Excel cũ, profile Chrome chứa session thật của người dùng và các tệp chứng thực Google Service Account chứa Private Key nhạy cảm.

3. **Unified Launcher:**
   - Đang đặt tại thư mục cha `D:\Tín\ABC\unified_launcher.py` và `D:\Tín\ABC\start_all.cmd`.
   - Điều phối 3 thành phần chạy song song an toàn: DashBoardD Backend (8000) + Test Engine Backend (18020) + Frontend Dev Server (5174) hoặc Web Prod (8000).

---

## 2. CẤU TRÚC THƯ MỤC THỰC TẾ

### A. Thư mục gốc `D:\Tín\ABC`
```
D:\Tín\ABC\
├── DashBoardD/                 # Thư mục dự án chính (Git Repo)
├── test/                       # Thư mục mã nguồn Test Engine (Không có Git)
├── start_all.cmd               # Script khởi động hợp nhất (gọi unified_launcher.py)
├── unified_launcher.py         # Bộ điều phối tiến trình Python không phụ thuộc bên ngoài
├── test.zip                    # Tệp nén lưu trữ backup của test (tạo 11/11/2026)
├── DashBoardD.7z, test.7z      # Các bản nén lịch sử cũ
└── Ann, DashBoardD1, GsAN, index, test1, Ticket (1) # Các thư mục tham chiếu / phụ trợ
```

### B. Thư mục `DashBoardD`
- **Tổng số tệp:** 44.686 files (~3.282 MB bao gồm cả `node_modules` và thư viện agent).
- **Mã nguồn thuần:** 1.049 files (~195 MB).
```
DashBoardD/
├── .git/                       # Git metadata (branch: main)
├── .gitignore                  # Quy tắc bỏ qua Git hiện tại
├── README.md, Dockerfile
├── backend/                    # FastAPI Backend (Port 8000)
│   ├── app/                    # Code chính (API routers, core, models, repositories, services)
│   │   ├── api/
│   │   │   ├── test_proxy.py   # [UNTRACKED] Reverse proxy kết nối cổng 18020
│   │   │   └── ...
│   │   ├── core/
│   │   │   └── auth.py         # [UNTRACKED] Xác thực Bearer Token
│   │   └── admin_config.json   # [TRACKED - MODIFIED] Chứa token và TOTP secret!
│   ├── tests/                  # Unit tests của DashBoardD (37 tests)
│   ├── requirements.txt        # Thư viện Python của DashBoardD
│   └── opsmonitor.db           # SQLite DB dữ liệu vận hành (được gitignore)
├── dashboard-app/              # React Frontend (Vite + Tailwind)
│   ├── src/
│   │   ├── pages/test/         # [UNTRACKED] 6 trang giao diện Test Control Center
│   │   ├── services/testApi/   # [UNTRACKED] Client kết nối API test engine
│   │   ├── context/            # [UNTRACKED] TestTaskContext
│   │   └── types/              # [UNTRACKED] Định nghĩa kiểu testEngine.ts
│   ├── dist/                   # Bản build production (được gitignore)
│   ├── node_modules/           # Thư viện npm (được gitignore)
│   └── package.json, vite.config.ts
├── docs/                       # Thư mục tài liệu báo cáo kỹ thuật (Phase 1 -> 8.4B)
└── cloudflared.exe, ngrok.exe  # [IGNORED] Binaries tunneling
```

### C. Thư mục `test`
- **Tổng số tệp:** 36.453 files (~2.759 MB bao gồm `desktop/node_modules`, `desktop/release`, `runtime`, `.venv`).
- **Mã nguồn thuần:** 1.321 files (~693 MB, trong đó `desktop/release` chiếm 656 MB).
```
test/
├── app/                        # Mã nguồn backend FastAPI (Port 18020)
│   ├── api/                    # Routes: camera, ftel_dvr, health, motion, settings, ticket, zalo
│   │   └── schemas/            # Pydantic schemas (common, ticket)
│   ├── services/               # 16 services nghiệp vụ (Zalo, Camera, Ticket, GSheet, Win32...)
│   ├── config.py               # Quản lý cấu hình runtime
│   └── paths.py                # Định nghĩa đường dẫn động dựa trên __file__
├── tests/                      # Thư mục kiểm thử tự động (api, unit, integration, golden, fixtures)
├── scripts/                    # Scripts vận hành, build và phát triển độc lập
│   ├── dev/run_standalone_backend.py  # Khởi chạy backend 18020 độc lập
│   └── start_backend.bat
├── desktop/                    # [LEGACY] Frontend Electron cũ (node_modules, src, release nsis)
├── runtime/                    # [DATA - SENSITIVE] Cực kỳ nhạy cảm:
│   ├── zalo_monitor.db         # SQLite DB lưu trữ tin nhắn Zalo thật
│   ├── zalo_web_profile/       # Chrome session đăng nhập Zalo thật
│   ├── chrome_profile/         # Chrome automation profile
│   ├── token.txt, app.log*     # Token và nhật ký vận hành
│   └── debug_screenshot.png
├── Checkcam.json, check-cam-*.json # [SECRETS] Google Cloud Service Account Private Key!
├── config.json                 # Cấu hình chứa URL sheets và đường dẫn local
├── chromedriver.exe, .zip      # [BINARY] Trình điều khiển Chrome (24 MB)
├── .env, requirements.txt, pyproject.toml
├── docs/                       # Hệ thống tài liệu lịch sử cũ (trùng lặp một phần với DashBoardD)
├── scratch/                    # 32 script ad-hoc từ các phase trước
├── build/, dist/, tmp/         # PyInstaller build outputs
└── ~30 script one-off tại gốc  # add_dump.py, fix_*.py, debug_*.py, patch_*.py, trace_*.py...
```

---

## 3. KẾT QUẢ GIT AUDIT

| Tiêu chí | Trạng thái | Chi tiết xác minh thực tế | Phân loại |
| :--- | :--- | :--- | :---: |
| **Repository Root** | `D:\Tín\ABC\DashBoardD` | Lệnh `git rev-parse --show-toplevel` xác nhận root tại `DashBoardD`. | **VERIFIED** |
| **Branch hiện tại** | `main` | Đang theo dõi `origin/main` (`https://github.com/tinmt2/DashBoardD.git`). | **VERIFIED** |
| **Commit mới nhất** | `ab13c1d` | `feat(employees): add 'Chuoi Inside' column...` (Không có commit lạ). | **VERIFIED** |
| **Working Tree** | Chưa sạch (Dirty) | Có **18 files modified** và **31 files untracked**. Đây là code tích hợp Phase 6-8 chưa commit. | **VERIFIED** |
| **Kiểm tra Git tại `test`** | **Không có Git** | Lệnh `git -C "d:\Tín\ABC\test" status` trả về: `fatal: not a git repository`. | **VERIFIED** |
| **Submodules** | Không có | Lệnh `git submodule status` không trả về submodule nào. | **VERIFIED** |
| **Nguy cơ rò rỉ bảo mật Git** | **RẤT CAO** | File `backend/app/admin_config.json` **đang được track trong Git** và chứa mật khẩu hash, token phiên, TOTP secret! | **VERIFIED** |

---

## 4. DANH SÁCH DEPENDENCY VÀ ĐƯỜNG DẪN NHẠY CẢM

### A. Phân tích Python Imports & Package Root
- **DashBoardD Backend:**
  - Khởi chạy từ thư mục `DashBoardD/backend` với lệnh: `uvicorn app.main:app`.
  - Mọi import bên trong đều có dạng `from app... import ...`.
- **Test Engine Backend:**
  - Khởi chạy từ thư mục `test` với lệnh: `uvicorn app.api.main:app`.
  - Mọi import bên trong đều có dạng `from app.paths import ...`, `from app.services... import ...`.
- **Đánh giá rủi ro xung đột import:**
  - Cả hai dự án đều dùng tên package gốc là `app`!
  - **KẾT LUẬN QUAN TRỌNG:** Nếu gộp hai dự án vào chung một tiến trình Python hoặc để chung một `sys.path`, module `app` của Test Engine và `app` của DashBoardD sẽ lập tức xung đột (Namespace Collision).
  - **GIẢI PHÁP [VERIFIED]:** Duy trì nguyên tắc kiến trúc số 6: **Hai backend chạy trên hai tiến trình riêng biệt** (Process Isolation). Khi chuyển `test` thành thư mục con `DashBoardD/test_engine`, tiến trình Test Engine sẽ đặt `cwd=DashBoardD/test_engine`, do đó `sys.path` của nó chỉ chứa `test_engine` và toàn bộ import `app.*` hoạt động hoàn hảo mà **không cần sửa một dòng import nào**.

### B. Phân tích đường dẫn tương đối và động trong mã nguồn
- `test/app/paths.py`:
  ```python
  BASE_DIR = Path(__file__).resolve().parent.parent
  ```
  `BASE_DIR` được tính động từ vị trí của file `paths.py` (lùi 2 cấp thư mục).
  - Khi ở `D:\Tín\ABC\test\app\paths.py` -> `BASE_DIR = D:\Tín\ABC\test`.
  - Khi chuyển sang `D:\Tín\ABC\DashBoardD\test_engine\app\paths.py` -> `BASE_DIR = D:\Tín\ABC\DashBoardD\test_engine`.
  => **Đường dẫn tự động thích ứng 100% không bị gãy!**

- `test/app/services/zalo_db.py`:
  ```python
  DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "runtime", "zalo_monitor.db")
  ```
  Tự động trỏ về `<engine_root>/runtime/zalo_monitor.db`.

- `test/app/services/zalo_web_adapter.py`:
  ```python
  self.profile_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "runtime", "zalo_web_profile")
  ```
  Tự động trỏ về `<engine_root>/runtime/zalo_web_profile`.

- `test/app/services/browser_manager.py`:
  ```python
  base_dir = Path(__file__).resolve().parent.parent.parent
  driver_path = base_dir / 'chromedriver.exe'
  ```
  Tự động trỏ về `<engine_root>/chromedriver.exe`.

- `test/app/services/gsheet_sync.py`:
  ```python
  str(BASE_DIR / _CFG.get("cred_file", "Checkcam.json"))
  ```
  Tự động trỏ về `<engine_root>/Checkcam.json`.

### C. Các đường dẫn Hardcoded phát hiện trong hệ thống
| Tệp | Vị trí / Dòng | Nội dung hardcoded | Đánh giá & Xử lý khi di chuyển |
| :--- | :--- | :--- | :--- |
| `unified_launcher.py` | Lòng 25-29 | `TEST_DIR = os.path.join(BASE_DIR, "test")`<br>`DASHBOARD_DIR = os.path.join(BASE_DIR, "DashBoardD")` | **BẮT BUỘC SỬA**: Đổi thành đường dẫn nội bộ trong `DashBoardD` khi chuyển launcher vào repo. |
| `test/config.json` | Dòng 4 | `"region_file": "D:/Tín/Lưu file LC/Danh sách vùng.xlsx"` | **NGOÀI REPO**: Trỏ vào thư mục cá nhân ngoài ABC, giữ nguyên hoặc chuyển thành đường dẫn cấu hình tương đối có thể tùy biến. |
| `test/config.json` | Dòng 5 | `"warehouse_file": "test_text.csv"` | Đường dẫn tương đối, giải quyết theo `cwd`. |
| `test/app/paths.py` | Dòng 19 | `PRIMARY_LOGS_DIR = Path(r"D:\test_app_logs")` | Trỏ vào ổ D ngoài thư mục dự án, có fallback an toàn vào `runtime/logs`. |
| `test/scripts/dev/run_standalone_backend.py` | Dòng 20 | `PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent` | Tự động tính toán theo cấu trúc thư mục, không bị ảnh hưởng. |
| `test/scripts/start_backend.bat` | Dòng 5 | `set VENV_PYTHON="%~dp0..\.venv\Scripts\python.exe"` | Phụ thuộc vào `.venv` cũ trong `test`. Nên cập nhật dùng `py -3.12`. |
| `test/scratch/*.py` | Nhiều dòng | `r"D:\Tín\ABC\test\..."` | Các script kiểm thử tạm thời cũ, không ảnh hưởng đến runtime sản xuất. |

### D. So sánh Dependencies Python & Npm
- **Python:**
  - Cả DashBoardD và Test Engine đều tương thích và đang chạy trên cùng môi trường `Python 3.12 (64-bit)` của máy tính.
  - Các gói thư viện: `fastapi`, `uvicorn`, `httpx`, `selenium`, `webdriver-manager`, `gspread`, `openpyxl`, `pandas`, `pydantic`, `sqlalchemy`, `psutil` đều đã được cài đặt đầy đủ trên môi trường global của `py -3.12`.
  - Không có xung đột phiên bản thư viện cốt lõi giữa hai backend.
- **Node.js / Npm:**
  - Máy tính sử dụng Node.js `v22.20.0`, npm `10.9.3`.
  - Toàn bộ frontend đã quy tụ về `DashBoardD/dashboard-app`. Bản build `dist/` đã có sẵn.

---

## 5. DANH SÁCH FILE CẦN BẢO VỆ TUYỆT ĐỐI (PROTECTED FILES)

> [!CAUTION]
> Các tệp và thư mục dưới đây chứa dữ liệu vận hành thực tế, bí mật chứng thực, phiên đăng nhập đang hoạt động hoặc tệp nhị phân nặng. **TUYỆT ĐỐI KHÔNG ĐƯỢC COMMIT VÀO GIT REPOSITORY!**

| Phân loại | Tên tệp / Đường dẫn | Lý do bảo vệ | Quy tắc xử lý bảo vệ |
| :--- | :--- | :--- | :--- |
| **Cơ sở dữ liệu SQLite** | `DashBoardD/backend/opsmonitor.db`<br>`DashBoardD/opsmonitor.db`<br>`test/runtime/zalo_monitor.db` | Chứa toàn bộ dữ liệu lịch sử sự vụ FPT Shop, Long Châu và 677+ tin nhắn Zalo thật. | Bắt buộc nằm trong `.gitignore` (`*.db`, `*.sqlite`, `runtime/`). Lưu trữ bản sao lưu trước khi thực hiện bất kỳ thao tác nào. |
| **Bí mật Chứng thực Google** | `test/Checkcam.json`<br>`test/check-cam-485509-9a51b6797327.json` | Chứa Private Key của Google Cloud Service Account dùng để đọc/ghi Google Sheets. | Bắt buộc cho vào `.gitignore`. Cung cấp file mẫu `Checkcam.example.json` thay thế. |
| **Phiên & Cookie Zalo thật** | `test/runtime/zalo_web_profile/` | Chứa phiên đăng nhập Chrome thật của người dùng vào Zalo Web (Session Cookies, LocalStorage). | Bắt buộc cho `runtime/` vào `.gitignore`. Di chuyển nguyên vẹn thư mục vật lý, không commit. |
| **Cấu hình & Token Admin** | `DashBoardD/backend/app/admin_config.json`<br>`test/runtime/token.txt` | Chứa hash mật khẩu admin, danh sách token đang hoạt động, TOTP secret. | **GỠ BỎ KHỎI GIT TRACKING** (`git rm --cached`), tạo `admin_config.example.json` để commit. |
| **Biến môi trường bí mật** | `DashBoardD/.env`<br>`test/.env` | Chứa API keys (Gemini API key, URLs hệ thống nội bộ). | Bắt buộc nằm trong `.gitignore`. Tạo `.env.example`. |
| **Trình điều khiển & Binary** | `test/chromedriver.exe`<br>`test/chromedriver.zip`<br>`DashBoardD/cloudflared.exe`<br>`DashBoardD/ngrok.exe` | Các file thực thi nhị phân có dung lượng từ 11MB - 25MB+. | Nằm trong `.gitignore` (`*.exe`, `*.zip`). |
| **Thư mục Build & Cache** | `test/.venv/`<br>`test/build/`, `test/dist/`<br>`test/desktop/release/` (656 MB)<br>`DashBoardD/dashboard-app/dist/`<br>`node_modules/`, `__pycache__/` | Tệp sinh tự động, làm phình to repository hàng gigabyte vô ích. | Bắt buộc nằm trong `.gitignore`. |

---

## 6. ĐỀ XUẤT KIẾN TRÚC ĐÍCH

### Phương án A: Monorepo phân tách dịch vụ trực tiếp (`DashBoardD/test_engine`) — [KHUYẾN NGHỊ]
```
DashBoardD/
├── .git/                                   # Git repository duy nhất quản lý toàn bộ
├── .gitignore                              # Cập nhật bổ sung đầy đủ các quy tắc bảo vệ
├── README.md
├── start_all.cmd                           # Launcher hợp nhất (chạy từ thư mục gốc repo)
├── unified_launcher.py                     # Quản lý vòng đời cả 2 backend và frontend
│
├── backend/                                # FastAPI Backend 1: Dashboard (Port 8000) [GIỮ NGUYÊN]
│   ├── app/                                # 100% code nghiệp vụ cũ không bị xáo trộn vị trí
│   │   ├── api/test_proxy.py               # Reverse Proxy định tuyến /api/test/* -> 18020
│   │   └── admin_config.example.json       # Bản mẫu cấu hình an toàn cho Git
│   ├── tests/                              # Pytest DashBoardD (37 tests)
│   └── requirements.txt
│
├── dashboard-app/                          # React Frontend (Port 5174 / Dist) [GIỮ NGUYÊN]
│   ├── src/
│   │   ├── pages/test/                     # Giao diện Test Engine tích hợp đầy đủ
│   │   └── services/testApi/               # Client kết nối qua Proxy
│   └── package.json
│
├── test_engine/                            # FastAPI Backend 2: Test Engine (Port 18020) [MỚI]
│   ├── app/                                # Code nghiệp vụ Camera, DVR, Ticket, Zalo, GSheet
│   │   ├── api/routes/                     # Các routers hiện tại của test
│   │   ├── services/                       # Các services hiện tại của test
│   │   ├── config.py                       # Cấu hình tự động thích ứng
│   │   └── paths.py                        # Đường dẫn tự động nhận diện root test_engine
│   ├── tests/                              # Bộ kiểm thử tự động của Test Engine
│   ├── scripts/                            # Scripts hỗ trợ dev và launcher độc lập
│   ├── config.example.json                 # Bản mẫu cấu hình cho Git
│   ├── config.json                         # [LOCAL] Cấu hình thực tế (được gitignore)
│   ├── Checkcam.json                       # [LOCAL] Google Secret (được gitignore)
│   ├── chromedriver.exe                    # [LOCAL] Binary driver (được gitignore)
│   ├── runtime/                            # [LOCAL] Data & session Zalo (được gitignore)
│   │   ├── zalo_monitor.db
│   │   └── zalo_web_profile/
│   ├── pyproject.toml
│   └── requirements.txt                    # Dependencies riêng của Test Engine
│
└── docs/                                   # Trung tâm tài liệu hợp nhất
    ├── dashboard/                          # Tài liệu thiết kế và vận hành Dashboard
    ├── test_engine/                        # Tài liệu nghiệp vụ Camera, DVR, Zalo (chọn lọc từ test/docs)
    └── reports/                            # Báo cáo các giai đoạn từ Phase 1 đến Phase 9
```

- **Ưu điểm vượt trội:**
  1. **Không gây tác động phụ (Zero Blast Radius):** Không di chuyển hay sửa đổi bất kỳ tệp tin nào của `backend/` và `dashboard-app/`. Toàn bộ commit history của Dashboard được giữ nguyên 100%.
  2. **Không xung đột Namespace:** Hai ứng dụng Python nằm ở hai thư mục tách biệt (`backend` và `test_engine`), chạy ở hai tiến trình độc lập, không bao giờ bị đụng độ package `app`.
  3. **Tự động tương thích đường dẫn:** Nhờ cơ chế `Path(__file__).resolve().parent.parent` của Test Engine, khi chuyển toàn bộ ruột của `test` vào `test_engine`, các dịch vụ tự động tìm thấy `runtime/`, `chromedriver.exe`, `Checkcam.json` mà không cần sửa code.
  4. **Rollback an toàn tuyệt đối:** Thư mục `D:\Tín\ABC\test` cũ có thể được đổi tên tạm thời thành `test_backup` để đối chiếu, nếu có bất kỳ sự cố nào chỉ cần đổi tên lại là hệ thống chạy bình thường.

### Phương án B: Tái cấu trúc phân cấp sâu (`DashBoardD/services/`) — [KHÔNG KHUYẾN NGHỊ]
```
DashBoardD/
├── services/
│   ├── dashboard_backend/                  # Chuyển backend vào đây
│   └── test_engine/                        # Chuyển test vào đây
├── apps/
│   └── dashboard_frontend/                 # Chuyển dashboard-app vào đây
└── ...
```
- **Lý do không khuyến nghị:**
  1. Phá vỡ toàn bộ cấu trúc Git hiện có, làm đứt gãy lịch sử `git blame` nếu không bật tùy chọn đặc biệt.
  2. Bắt buộc phải cập nhật lại hàng loạt file cấu hình: Dockerfile, Vite base path, package.json scripts, path imports trong các file tests `conftest.py`.
  3. Rủi ro hồi quy phát sinh lỗi cao gấp nhiều lần so với Phương án A nhưng không đem lại giá trị chức năng gia tăng nào.

---

## 7. BẢNG CÁC THAY ĐỔI DỰ KIẾN (KHI ĐƯỢC PHÊ DUYỆT)

| STT | Đối tượng | Hành động | Nguồn hiện tại | Đích dự kiến | Ghi chú & Đảm bảo an toàn |
| :---: | :--- | :---: | :--- | :--- | :--- |
| **1** | Dashboard Backend | **GIỮ NGUYÊN** | `DashBoardD/backend` | `DashBoardD/backend` | Giữ nguyên 100% vị trí, code và test. |
| **2** | Dashboard Frontend | **GIỮ NGUYÊN** | `DashBoardD/dashboard-app` | `DashBoardD/dashboard-app` | Giữ nguyên 100% vị trí, code và build. |
| **3** | Test Engine App Code | **DI CHUYỂN** | `test/app/` | `DashBoardD/test_engine/app/` | Di chuyển toàn bộ routes, services, schemas. |
| **4** | Test Engine Tests | **DI CHUYỂN** | `test/tests/` | `DashBoardD/test_engine/tests/` | Di chuyển unit, api, integration tests. |
| **5** | Test Engine Scripts | **CHỌN LỌC** | `test/scripts/` | `DashBoardD/test_engine/scripts/` | Giữ `dev/`, `build/`; loại bỏ sandbox rác. |
| **6** | Test Engine Config | **DI CHUYỂN** | `test/config.json` | `DashBoardD/test_engine/config.json` | Giữ file local, tạo `config.example.json` cho Git. |
| **7** | Google Secret Key | **DI CHUYỂN LOCAL** | `test/Checkcam.json` | `DashBoardD/test_engine/Checkcam.json` | Di chuyển local, **KHÔNG COMMIT GIT**. |
| **8** | Chrome Driver | **DI CHUYỂN LOCAL** | `test/chromedriver.exe` | `DashBoardD/test_engine/chromedriver.exe` | Di chuyển local, **KHÔNG COMMIT GIT**. |
| **9** | Test Runtime & Data | **DI CHUYỂN LOCAL** | `test/runtime/` | `DashBoardD/test_engine/runtime/` | Chứa `zalo_monitor.db` & session Zalo, **KHÔNG COMMIT GIT**. |
| **10** | Unified Launcher | **CẬP NHẬT & CHUYỂN** | `ABC/unified_launcher.py`<br>`ABC/start_all.cmd` | `DashBoardD/unified_launcher.py`<br>`DashBoardD/start_all.cmd` | Cập nhật `TEST_DIR = test_engine`, đặt wrapper chuyển tiếp tại `ABC`. |
| **11** | Admin Config Security | **GỠ BỎ KHỎI GIT** | `DashBoardD/backend/app/admin_config.json` | Local file (Gitignore) | `git rm --cached`, tạo `admin_config.example.json` đưa lên Git. |
| **12** | Quy tắc `.gitignore` | **CẬP NHẬT** | `DashBoardD/.gitignore` | `DashBoardD/.gitignore` | Thêm quy tắc bảo vệ `test_engine/runtime/`, `*.json` nhạy cảm, `*.zip`, `.ruff_cache`. |
| **13** | Tài liệu Test cũ | **HỢP NHẤT** | `test/docs/` | `DashBoardD/docs/test_engine/` | Chọn lọc tài liệu kiến trúc, loại bỏ các file trùng lặp. |
| **14** | One-off patch scripts | **LƯU TRỮ (ARCHIVE)** | `test/*.py` (~30 file patch/debug) | `D:\Tín\ABC\test_archive_patches/` hoặc giữ nguyên tại bản backup | Không đưa vào repository chính để tránh ô nhiễm code. |
| **15** | Legacy Electron Desktop | **LOẠI BỎ KHỎI PROD** | `test/desktop/` | Lưu trữ trong backup ngoài Git | Toàn bộ tính năng đã có trong Web Dashboard. Không commit 656MB installer release. |

---

## 8. PHÂN TÍCH RỦI RO VÀ PHƯƠNG ÁN ROLLBACK

### A. Ma trận rủi ro tiềm ẩn

| Rủi ro tiềm ẩn | Mức độ | Khả năng xảy ra | Biện pháp kiểm soát & Phòng ngừa |
| :--- | :---: | :---: | :--- |
| **1. Mất mát session Zalo Web hoặc DB Zalo** | **CRITICAL** | Thấp | Sao lưu toàn bộ thư mục `test/runtime` ra vị trí an toàn trước khi di chuyển. Không dùng lệnh cut/delete nguy hiểm; sử dụng copy có kiểm tra hash hoặc lưu bản zip `test.zip`. |
| **2. Vô tình commit Private Key hoặc Token lên GitHub** | **CRITICAL** | Trung bình | Cập nhật file `.gitignore` ĐẦU TIÊN trước khi copy code; chạy lệnh `git status` kiểm tra kỹ danh sách staged files trước mọi lệnh `git commit`. |
| **3. Lệch đường dẫn làm gãy tiến trình quét Camera / Zalo** | **HIGH** | Thấp | Test Engine sử dụng đường dẫn tương đối động (`Path(__file__)`), đã được xác minh tự động khớp với thư mục con `test_engine`. |
| **4. Gãy kết nối Reverse Proxy `/api/test/*`** | **MEDIUM** | Rất thấp | Cổng 18020 được giữ nguyên. Proxy giao tiếp qua TCP loopback `127.0.0.1:18020` hoàn toàn độc lập với vị trí thư mục trên đĩa. |
| **5. Xung đột môi trường Python hoặc thiếu thư viện** | **LOW** | Rất thấp | Cả hai tiến trình đều được xác minh chạy trên môi trường `Python 3.12 (64-bit)` của máy và đã có sẵn đầy đủ packages. |

### B. Quy trình Rollback dự phòng (Fail-safe Rollback Procedure)
Nếu sau khi hợp nhất phát sinh bất kỳ lỗi nghiêm trọng nào không thể khắc phục ngay:
1. **Dừng toàn bộ tiến trình:** Đóng cửa sổ terminal launcher hoặc chạy `taskkill /F /IM python.exe` / `taskkill /F /IM uvicorn.exe`.
2. **Khôi phục trạng thái Git:**
   ```bash
   cd D:\Tín\ABC\DashBoardD
   git checkout -- .
   git clean -fd test_engine/
   ```
3. **Phục hồi hoạt động từ thư mục `test` gốc:**
   - Thư mục `D:\Tín\ABC\test` ban đầu được giữ nguyên vẹn (chỉ đọc) trong suốt quá trình migration.
   - Chạy lại `D:\Tín\ABC\start_all.cmd` ban đầu -> Toàn bộ hệ thống lập tức hoạt động lại bình thường trong vòng 10 giây.

---

## 9. CÁC LỆNH KIỂM TRA AN TOÀN (SAFE VALIDATION COMMANDS)

Các lệnh kiểm tra hoàn toàn ở chế độ CHỈ ĐỌC (Read-only), không gây tác dụng phụ, dùng để kiểm tra hệ thống trước và sau khi được phê duyệt:

### 1. Kiểm tra trạng thái Git và phát hiện tệp nhạy cảm bị theo dõi:
```powershell
# Kiểm tra file nhạy cảm có bị git theo dõi không
git -C "D:\Tín\ABC\DashBoardD" ls-files | Select-String -Pattern "admin_config\.json|Checkcam|\.db|\.env"
```

### 2. Kiểm tra tính toàn vẹn của mã nguồn Frontend (Lint & Type-check):
```powershell
# Kiểm tra cú pháp và kiểu TypeScript mà không phát sinh file rác
cd "D:\Tín\ABC\DashBoardD\dashboard-app"
npx oxlint
npx tsc -b --noEmit
```

### 3. Kiểm tra bộ kiểm thử đơn vị Backend DashBoardD (Mock hoàn toàn, không đụng mạng):
```powershell
cd "D:\Tín\ABC\DashBoardD\backend"
py -3.12 -m pytest tests/unit/test_test_proxy.py tests/unit/test_auto_sync_api.py -v
```

### 4. Kiểm tra bộ kiểm thử Win32 Window Activator của Test Engine:
```powershell
cd "D:\Tín\ABC\test"
py -3.12 -m pytest tests/unit/test_window_activator.py tests/unit/test_zalo_app_mode_activation.py -v
```

### 5. Kiểm tra trạng thái sức khỏe cổng và dịch vụ không xâm lấn:
```powershell
# Chạy chế độ kiểm tra sức khỏe read-only của launcher
py -3.12 "D:\Tín\ABC\unified_launcher.py" --status
```

---

## 10. DANH SÁCH ĐIỂM CHƯA XÁC MINH VÀ PHÂN LOẠI MINH BẠCH

Theo nguyên tắc bắt buộc số 9 và 10, toàn bộ các phát hiện được phân định rõ ràng như sau:

| Hạng mục | Kết luận | Căn cứ kiểm tra |
| :--- | :---: | :--- |
| **Trạng thái Git của `DashBoardD`** | **VERIFIED** | Đã kiểm tra trực tiếp qua `git status`, `git branch`, `git log`, `git remote`. Xác nhận 18 file modified, 31 file untracked. |
| **Trạng thái Git của `test`** | **VERIFIED** | Đã kiểm tra `git status` tại `test` và quét tìm file `.git*`. Xác nhận 100% không có Git repository riêng. |
| **Đường dẫn động trong Test Engine** | **VERIFIED** | Đã đọc mã nguồn `paths.py`, `zalo_db.py`, `browser_manager.py`. Tất cả đều sử dụng `__file__` và tự động tương thích khi vào `test_engine`. |
| **Hoạt động của Reverse Proxy `/api/test/*`** | **VERIFIED** | Đã đọc mã nguồn `test_proxy.py` và test `test_test_proxy.py`. Kết nối giữa 8000 và 18020 là độc lập hoàn toàn với cấu trúc thư mục đĩa. |
| **Rò rỉ bảo mật `admin_config.json`** | **VERIFIED** | Đã xem trực tiếp `git diff backend/app/admin_config.json`, xác nhận file chứa live token hash và TOTP secret bị Git theo dõi. |
| **Mục đích của ~30 script one-off tại `test/`** | **PARTIAL** | Suy luận từ tên (`fix_*.py`, `debug_*.py`, `patch_*.py`) và nội dung file là các script can thiệp nóng cục bộ trong quá khứ. Cần xác nhận từ chủ dự án xem có cần giữ lại để tham khảo hay không. |
| **Sự cần thiết của `test/desktop` (Electron)** | **PARTIAL** | Đã xác minh toàn bộ 6 trang nghiệp vụ đã có trên React Web. Tuy nhiên chưa thể xác nhận 100% chủ dự án có còn muốn đóng gói ứng dụng `.exe` desktop riêng từ mã nguồn Electron này nữa hay không. |
| **Tệp `D:/Tín/Lưu file LC/Danh sách vùng.xlsx`** | **UNVERIFIED** | Nằm ngoài thư mục `ABC`, được cấu hình trong `config.json`. Chưa thể xác minh tệp này có đang được sử dụng thường xuyên hay không vì thuộc dữ liệu ngoài phạm vi. |

---

## 11. CHECKLIST NGHIỆM THU SAU KHI ĐƯỢC PHÊ DUYỆT (POST-APPROVAL CHECKLIST)

Khi chủ dự án đồng ý kế hoạch và phê duyệt bước sang giai đoạn thực thi (Migration Phase), các bước nghiệm thu sau sẽ được thực hiện tuần tự:

- [ ] **Giai đoạn 1: Bảo toàn dữ liệu (Safety First)**
  - [ ] Nén toàn bộ thư mục `test/runtime` thành `runtime_backup.zip`.
  - [ ] Kiểm tra working tree của `DashBoardD` bằng `git status`.
- [ ] **Giai đoạn 2: Gia cố Bảo mật (.gitignore)**
  - [ ] Cập nhật `.gitignore` tại `DashBoardD` loại bỏ `test_engine/runtime/`, `*cred*.json`, `Checkcam.json`, `admin_config.json`, `*.zip`.
  - [ ] Chạy `git rm --cached backend/app/admin_config.json` và tạo `admin_config.example.json`.
- [ ] **Giai đoạn 3: Di chuyển mã nguồn có chọn lọc**
  - [ ] Tạo thư mục `DashBoardD/test_engine/`.
  - [ ] Copy `app/`, `tests/`, `scripts/`, `pyproject.toml`, `requirements.txt` vào `test_engine/`.
  - [ ] Copy `runtime/`, `Checkcam.json`, `config.json`, `chromedriver.exe` vào `test_engine/` (ở trạng thái không track Git).
  - [ ] Tạo `test_engine/config.example.json`.
- [ ] **Giai đoạn 4: Cập nhật Unified Launcher**
  - [ ] Chuyển `unified_launcher.py` và `start_all.cmd` vào `DashBoardD`.
  - [ ] Cập nhật biến `TEST_DIR = os.path.join(BASE_DIR, "test_engine")`.
  - [ ] Để lại script chuyển tiếp nhẹ tại `D:\Tín\ABC\start_all.cmd`.
- [ ] **Giai đoạn 5: Kiểm thử hồi quy toàn diện (Regression Testing)**
  - [ ] Chạy `py -3.12 -m pytest backend/tests` tại DashBoardD -> Đạt 100%.
  - [ ] Chạy `py -3.12 -m pytest test_engine/tests/unit` tại DashBoardD -> Đạt 100%.
  - [ ] Khởi chạy `unified_launcher.py --status` -> Cả 3 cổng 8000, 18020, 5174 đều ONLINE và trả lời đúng Health Check.
  - [ ] Mở trình duyệt kiểm tra các tab Check Camera, Ticket SSC, Zalo Monitor qua giao diện Dashboard.
- [ ] **Giai đoạn 6: Commit Git chuẩn hóa**
  - [ ] Kiểm tra lại `git status` đảm bảo **KHÔNG CÓ** file runtime, database, secret hay binary bị add nhầm.
  - [ ] Thực hiện commit hoàn thiện hợp nhất mã nguồn.
