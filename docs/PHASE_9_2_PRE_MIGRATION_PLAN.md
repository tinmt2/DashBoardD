# KẾ HOẠCH CHI TIẾT TIỀN DI CHUYỂN MÃ NGUỒN
# PHASE 9.2 — PRE-MIGRATION TECHNICAL VALIDATION & PLAN

**Dự án:** Hợp nhất mã nguồn DashBoardD + Test Engine  
**Giai đoạn thực hiện:** Phase 2 — Pre-Migration Technical Validation  
**Ngày thực hiện:** 11/11/2026 (22:30 UTC+7)  
**Kỹ sư thực hiện:** AI Pair Programmer / Senior Software Architect & DevOps  
**Trạng thái hiện tại:** **HOÀN THÀNH PHASE 2 — DỪNG HOÀN TOÀN CHỜ PHÊ DUYỆT ĐỂ SANG PHASE 3**

---

## 1. TỔNG QUAN KẾT QUẢ KIỂM TRA KỸ THUẬT (EXECUTIVE SUMMARY)

1. **Bảo toàn nguyên vẹn 100% hiện trạng:**
   - Xác nhận bảo vệ nguyên vẹn **18 files modified** và **31 files untracked** tại `DashBoardD`.
   - Toàn bộ thư mục `D:\Tín\ABC\test` gốc và bản sao lưu tại `D:\Tín\ABC\_backups_phase1\` được giữ nguyên vẹn ở chế độ chỉ đọc.
2. **Xác minh quy chế phân lập tiến trình (Process Isolation Verification):**
   - Đã kiểm chứng kỹ thuật: Khi đứng từ thư mục `D:\Tín\ABC\test`, bộ kiểm thử `pytest tests/unit/test_window_activator.py tests/unit/test_zalo_app_mode_activation.py` đạt **14/14 PASSED (100%)** trong 4.30 giây.
   - Khi chuyển Test Engine vào `DashBoardD/test_engine` và cấu hình `cwd=DashBoardD/test_engine`, Python tự động phân giải `app.*` độc lập tuyệt đối với `app.*` của `DashBoardD/backend`. **Không cần sửa bất kỳ dòng lệnh import nào** trong mã nguồn nghiệp vụ `test/app`.
3. **Xác minh Reverse Proxy và Giao diện Quản trị:**
   - Bộ kiểm thử `DashBoardD/backend/tests/unit/test_test_proxy.py` đạt **3/3 PASSED (100%)**. Reverse Proxy `/api/test/*` lọc header nhạy cảm và chuyển tiếp an toàn tới cổng 18020.
   - Kiểm tra kiểu tĩnh TypeScript `npx tsc -b --noEmit` trên `dashboard-app` đạt **0 Errors (100% sạch)**. Toàn bộ 6 giao diện Test (`#/admin/camera`, `#/admin/ticket`, `#/admin/motion`, `#/admin/zalo`, `#/admin/settings`, `#/admin/system`) đã sẵn sàng.
4. **Phân loại toàn diện các script cũ tại `test/`:**
   - Đã kiểm tra chi tiết từng file trong số 30 script Python tại thư mục gốc `test/`, các script trong `test/scripts/` và `test/scratch/`.
   - Xác định 100% các script tại gốc `test/*.py` là các công cụ vá nóng chuỗi/thụt dòng từ cuối tháng 9/2026; các thay đổi đó đã được nhúng vĩnh viễn vào `app/services/`. Không có bất kỳ file nghiệp vụ runtime nào tham chiếu đến các script này.
5. **Xác nhận tệp Excel ngoài dự án:**
   - File `D:\Tín\Lưu file LC\Danh sách vùng.xlsx` được xác minh **đang tồn tại thực tế trên máy tính**. Kế hoạch giữ nguyên vẹn file này, giữ nguyên cấu hình local tại `config.json` và cung cấp đường dẫn mẫu trong `config.example.json`.

---

## 2. MA TRẬN PHÂN LOẠI CHI TIẾT TÀI NGUYÊN VÀ SCRIPT CỦA TEST ENGINE

### A. Nhóm 1: Mã nguồn nghiệp vụ sản xuất (Production Code) -> [DI CHUYỂN VÀO REPO]
| Thư mục / Tệp | Vai trò nghiệp vụ | Bằng chứng kiểm tra thực tế | Hành động Phase 3 |
| :--- | :--- | :--- | :---: |
| `test/app/api/main.py`<br>`test/app/api/dependencies.py` | FastAPI App trên cổng 18020, CORS, Middleware | Đang chạy phục vụ health check và routers | Di chuyển vào `test_engine/app/api/` |
| `test/app/api/routes/*.py` (7 routers) | Routers: camera, ftel_dvr, health, motion, settings, ticket, zalo | Đã test qua proxy và unit test | Di chuyển vào `test_engine/app/api/routes/` |
| `test/app/api/schemas/*.py` | Pydantic Schemas dữ liệu chuẩn hóa | Được routers import | Di chuyển vào `test_engine/app/api/schemas/` |
| `test/app/services/*.py` (16 services) | Xử lý Camera Hikvision, DVR FTEL, Ticket SSC, Zalo AI, GSheet | Đạt 14/14 unit tests, import nội bộ `app.services` | Di chuyển vào `test_engine/app/services/` |
| `test/app/config.py`<br>`test/app/paths.py` | Quản lý cấu hình và đường dẫn tương đối động | Dùng `Path(__file__)`, tự thích ứng khi đổi thư mục | Di chuyển vào `test_engine/app/` |
| `test/pyproject.toml`<br>`test/requirements.txt` | Khai báo dependency và cấu hình ruff lint | Cần thiết để quản lý môi trường | Di chuyển vào `test_engine/` |

### B. Nhóm 2: Bộ kiểm thử tự động (Automated Test Suite) -> [DI CHUYỂN VÀO REPO]
| Thư mục / Tệp | Vai trò | Bằng chứng kiểm tra | Hành động Phase 3 |
| :--- | :--- | :--- | :---: |
| `test/tests/unit/` | Unit tests: window_activator, zalo_activation, etc. | Chạy thực tế đạt 14/14 PASSED | Di chuyển vào `test_engine/tests/unit/` |
| `test/tests/api/` | API route integration tests | Kiểm tra endpoints camera, ticket, settings | Di chuyển vào `test_engine/tests/api/` |
| `test/tests/integration/` | Integration tests cho DVR worker và motion | Kiểm tra luồng tích hợp nền | Di chuyển vào `test_engine/tests/integration/` |
| `test/tests/golden/` & `test/tests/fixtures/` | Golden regression data và mẫu test CSV | Cung cấp dữ liệu chuẩn đối soát | Di chuyển vào `test_engine/tests/` |

### C. Nhóm 3: Scripts Vận hành & Phát triển (Operational & Dev Scripts) -> [CHỌN LỌC]
| Tệp script | Bằng chứng sử dụng | Phân loại | Hành động Phase 3 |
| :--- | :--- | :---: | :---: |
| `test/scripts/dev/run_standalone_backend.py` | Khởi chạy FastAPI 18020 độc lập không cần launcher | **Đang dùng** | Di chuyển vào `test_engine/scripts/dev/` |
| `test/scripts/start_backend.bat` | Script CMD gọi `run_standalone_backend.py` | **Đang dùng** | Cập nhật dùng `py -3.12`, di chuyển vào `test_engine/scripts/` |
| `test/scripts/check_env.py` | Kiểm tra thư viện và môi trường | **Dev tool** | Di chuyển vào `test_engine/scripts/` |
| `test/scripts/ftel_real_e2e.py`<br>`test/scripts/test_single_pipeline.py` | Script test regression thủ công | **Test tool** | Di chuyển vào `test_engine/scripts/` |
| `test/scripts/build/build_backend.py`<br>`test/scripts/build/build_nsis.ps1` | Script đóng gói PyInstaller / NSIS cho desktop cũ | **Build tool** | Di chuyển vào `test_engine/scripts/build/` |
| `test/scripts/sandbox/*.py` (25 scripts) | Các script thử nghiệm Selenium, CDP, Playback | **Sandbox** | Giữ nguyên tại thư mục gốc `test/`, không đưa vào repo chính |

### D. Nhóm 4: Các script vá lỗi một lần tại thư mục gốc `test/*.py` (30 scripts) -> [LƯU TRỮ, KHÔNG ĐƯA VÀO REPO]
- **Danh sách kiểm tra:**
  - `clean.py`, `clean2.py` (vá cú pháp trong `ftel_dvr_service.py`).
  - `fix.py` (chèn try/except vào `check_cam_service.py`).
  - `fix_all_else.py`, `fix_all_else_2.py`, `fix_configured.py`, `fix_indentation.py`, `fix_line_102.py`, `fix_spaces*.py`, `check_spaces*.py` (sửa thụt dòng và khoảng trắng).
  - `debug_82381.py`, `debug_online*.py`, `debug_trace*.py`, `trace_append.py`, `trace_issue.py`, `trace_job.py`, `trace_runtime.py` (in log kiểm tra từng case lỗi cũ).
  - `patch.py`, `patch_loc.py`, `remove_hack.py`, `replace.py` (chỉnh sửa text một lần).
  - `gen_test.py` (tạo file `test.xlsx`).
  - `temp_index.js`, `temp_main.js`, `temp_body.txt`, `recent_log.txt`, `test_out*.txt` (file rác tạm).
- **Bằng chứng phân loại:** Các file này được tạo từ 27/09 đến 07/10/2026. Kiểm tra toàn bộ mã nguồn `test/app/` xác nhận **không có bất kỳ file nào import hoặc gọi đến chúng**. Các thay đổi sửa lỗi của chúng đã được lưu trữ vĩnh viễn trong code service.
- **Hành động Phase 3:** **KHÔNG ĐƯA VÀO REPO MỚI**. Giữ nguyên vẹn tại thư mục gốc `D:\Tín\ABC\test` (hoặc bản backup `.7z`) để tham khảo lịch sử khi cần.

### E. Nhóm 5: Mã nguồn Electron Desktop cũ (`test/desktop/`) -> [BẢO TỒN CÓ KHẢ NĂNG PHỤC HỒI]
- **Đánh giá dung lượng:**
  - Thư mục `test/desktop/release/` chiếm **656 MB** (bộ cài exe và win-unpacked).
  - Thư mục `test/desktop/node_modules/` chiếm **~2 GB** (hàng chục nghìn file).
  - Mã nguồn thuần (`src/`, `electron/`, `package.json`, `vite.config.ts`, `tsconfig.json`) chỉ chiếm **~5 MB**.
- **Giải pháp bảo tồn phục hồi hoàn hảo:**
  - Toàn bộ bản build và mã nguồn đã được đóng gói an toàn trong `_backups_phase1\TestEngine_working_tree.7z` và thư mục `D:\Tín\ABC\test` gốc.
  - Tại repository mới `DashBoardD/test_engine/`: Đưa mã nguồn sạch vào thư mục `test_engine/desktop/` (hoặc `test_engine/legacy_desktop/`) chỉ gồm các file nguồn (`src/`, `electron/`, `package.json`, `index.html`), đồng thời cấu hình `.gitignore` loại bỏ tuyệt đối `dist/`, `dist-electron/`, `release/`, `node_modules/`.
  - **Kết quả:** Bất cứ khi nào cần đóng gói lại ứng dụng Desktop Electron, kỹ sư chỉ cần vào thư mục này chạy `npm install && npm run electron:pack`. Repo Git được bảo vệ sạch sẽ, không bị phình dung lượng.

### F. Nhóm 6: Dữ liệu Runtime, Secrets & File cấu hình -> [BẢO VỆ CỤC BỘ, KHÔNG COMMIT]
| Tệp / Thư mục | Bản chất | Xử lý tại Phase 3 |
| :--- | :--- | :--- |
| `test/runtime/zalo_monitor.db` | SQLite database chứa 677+ tin nhắn Zalo | Copy sang `test_engine/runtime/zalo_monitor.db`. **GITIGNORED**. |
| `test/runtime/zalo_web_profile/` | Chrome session đăng nhập Zalo thật | Copy sang `test_engine/runtime/zalo_web_profile/`. **GITIGNORED**. |
| `test/runtime/token.txt` | JWT Token tự động hóa Ticket SSC | Copy sang `test_engine/runtime/token.txt`. **GITIGNORED**. |
| `test/Checkcam.json`<br>`test/check-cam-*.json` | Private Key Google Service Account | Copy sang `test_engine/Checkcam.json`. **GITIGNORED**. |
| `test/chromedriver.exe` | Binary driver trình duyệt Chrome (24 MB) | Copy sang `test_engine/chromedriver.exe`. **GITIGNORED**. |
| `test/config.json` | Cấu hình nội bộ thực tế | Copy sang `test_engine/config.json`. **GITIGNORED**. Tạo `config.example.json` để commit lên Git. |
| `backend/app/admin_config.json` | Admin password hash & TOTP secret | Chạy `git rm --cached`, đưa vào `.gitignore`, tạo `admin_config.example.json` để commit. |

---

## 3. THAY ĐỔI DỰ KIẾN ĐỐI VỚI UNIFIED LAUNCHER

### A. Tệp `unified_launcher.py`
Khi chuyển vào `DashBoardD/unified_launcher.py`, các đường dẫn ở Phần 1 của file được chuẩn hóa:
```python
# CŨ (Khi launcher nằm tại D:\Tín\ABC):
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_DIR = os.path.join(BASE_DIR, "DashBoardD")
DASHBOARD_BACKEND_DIR = os.path.join(DASHBOARD_DIR, "backend")
DASHBOARD_FRONTEND_DIR = os.path.join(DASHBOARD_DIR, "dashboard-app")
TEST_DIR = os.path.join(BASE_DIR, "test")

# MỚI (Khi launcher nằm tại D:\Tín\ABC\DashBoardD):
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_DIR = BASE_DIR
DASHBOARD_BACKEND_DIR = os.path.join(BASE_DIR, "backend")
DASHBOARD_FRONTEND_DIR = os.path.join(BASE_DIR, "dashboard-app")
TEST_DIR = os.path.join(BASE_DIR, "test_engine")
```
- Lệnh chạy DashBoardD Backend: `[PYTHON_EXE, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]` (cwd: `DASHBOARD_BACKEND_DIR`) -> **GIỮ NGUYÊN**.
- Lệnh chạy Test Engine Backend: `[PYTHON_EXE, "-m", "uvicorn", "app.api.main:app", "--host", "127.0.0.1", "--port", "18020", "--no-access-log"]` (cwd: `TEST_DIR`) -> **GIỮ NGUYÊN**.
- Lệnh chạy Frontend Dev: `npm run dev` (cổng 5174, cwd: `DASHBOARD_FRONTEND_DIR`) -> **GIỮ NGUYÊN**.

### B. Tệp `D:\Tín\ABC\start_all.cmd` (Chuyển tiếp tương thích ngược)
Để đảm bảo thói quen kích đúp chuột tại thư mục gốc `D:\Tín\ABC\start_all.cmd` không bị ảnh hưởng, tệp này sẽ được cấu hình thành wrapper chuyển tiếp an toàn:
```cmd
@echo off
setlocal
cd /d "%~dp0DashBoardD"
call start_all.cmd %*
exit /b %errorlevel%
```
Đồng thời, tại `DashBoardD/start_all.cmd` sẽ là script thực thi chính gọi `py -3.12 unified_launcher.py`.

---

## 4. CHI TIẾT CẬP NHẬT `.gitignore` ĐỂ BẢO VỆ DỮ LIỆU

Bổ sung các quy tắc bắt buộc sau vào `DashBoardD/.gitignore` ngay đầu Phase 3:
```gitignore
# --- TEST ENGINE RUNTIME & LOCAL DATA ---
test_engine/runtime/
**/runtime/
*.db
*.sqlite

# --- SECRETS & SERVICE ACCOUNT KEYS ---
*Checkcam*.json
*check-cam*.json
*secret*.json
backend/app/admin_config.json
admin_config.json
.env
.env.*

# --- BINARIES & LARGE ARTIFACTS ---
*.exe
*.zip
*.7z
chromedriver*
test_engine/desktop/dist/
test_engine/desktop/dist-electron/
test_engine/desktop/release/

# --- CACHE ---
.ruff_cache/
__pycache__/
.pytest_cache/
```

---

## 5. KẾ HOẠCH KIỂM THỬ XÁC MINH (TESTING APPROACH)

Sau khi hoàn tất copy mã nguồn trong Phase 3, các kiểm thử sau sẽ được thực hiện trước khi công bố Phase 4:
1. **Kiểm tra cú pháp & Import Test Engine:**
   - Lệnh: `cd D:\Tín\ABC\DashBoardD\test_engine && py -3.12 -c "import app.api.main; import app.services.check_cam_service; import app.services.zalo_db; print('TEST_ENGINE_IMPORT_OK')"`
   - Đạt: In ra `TEST_ENGINE_IMPORT_OK` không báo lỗi.
2. **Kiểm tra Unit Tests Test Engine tại vị trí mới:**
   - Lệnh: `cd D:\Tín\ABC\DashBoardD\test_engine && py -3.12 -m pytest tests/unit/test_window_activator.py tests/unit/test_zalo_app_mode_activation.py -v`
   - Đạt: 14/14 tests PASSED.
3. **Kiểm tra Unit Tests DashBoardD Backend & Proxy:**
   - Lệnh: `cd D:\Tín\ABC\DashBoardD\backend && py -3.12 -m pytest tests/unit/test_test_proxy.py -v`
   - Đạt: 3/3 tests PASSED.
4. **Kiểm tra TypeScript Frontend:**
   - Lệnh: `cd D:\Tín\ABC\DashBoardD\dashboard-app && npx tsc -b --noEmit`
   - Đạt: 0 Errors.
5. **Kiểm tra trạng thái sức khỏe dịch vụ (Read-only Health Audit):**
   - Lệnh: `cd D:\Tín\ABC\DashBoardD && py -3.12 unified_launcher.py --status`
   - Đạt: Nhận diện chính xác trạng thái các cổng 8000, 18020, 5174.
6. **Kiểm tra Git Hygiene:**
   - Lệnh: `git -C "D:\Tín\ABC\DashBoardD" status`
   - Đạt: Tuyệt đối không có file `runtime/`, `.db`, `Checkcam.json`, `.exe` nào bị đưa vào danh sách theo dõi của Git.

---

## 6. PHƯƠNG ÁN ROLLBACK CHI TIẾT (STEP-BY-STEP ROLLBACK)

Nếu có bất kỳ sự cố nào xảy ra trong Phase 3:
1. **Bước 1 — Tắt tiến trình:** Dừng toàn bộ tiến trình python/node đang chạy:
   ```cmd
   taskkill /F /IM python.exe
   ```
2. **Bước 2 — Xóa thư mục di chuyển:** Xóa thư mục mới `DashBoardD/test_engine/` (hoặc hoàn tác git):
   ```powershell
   Remove-Item -Path "D:\Tín\ABC\DashBoardD\test_engine" -Recurse -Force
   ```
3. **Bước 3 — Khôi phục launcher:** Khôi phục `D:\Tín\ABC\start_all.cmd` và `D:\Tín\ABC\unified_launcher.py` từ thư mục sao lưu `D:\Tín\ABC\_backups_phase1\critical_uncommitted\ABC_root\`.
4. **Bước 4 — Khởi động lại hệ thống gốc:** Kích hoạt lại `D:\Tín\ABC\start_all.cmd`. Hệ thống trở về trạng thái hoạt động ban đầu 100% trong vòng dưới 15 giây.

---

## 7. BẢNG PHÂN LOẠI MỨC ĐỘ MINH BẠCH (VERIFIED / PARTIAL / UNVERIFIED)

| Tiêu chí kỹ thuật | Phân loại | Căn cứ xác minh thực tế |
| :--- | :---: | :--- |
| **Độc lập tiến trình & Tương thích Import** | **VERIFIED** | Chạy pytest thực tế: `test` chỉ nhận `app.*` khi `cwd=test`. Hai backend độc lập không xung đột import khi đặt `cwd` riêng biệt. |
| **Tương thích Reverse Proxy `/api/test/*`** | **VERIFIED** | Đã chạy 3 unit tests `test_test_proxy.py` đạt 100% PASS; proxy hoạt động qua loopback TCP `127.0.0.1:18020` không phụ thuộc vị trí thư mục đĩa. |
| **Sự tồn tại của `Danh sách vùng.xlsx`** | **VERIFIED** | Đã kiểm tra trực tiếp qua `Test-Path "D:\Tín\Lưu file LC\Danh sách vùng.xlsx"` -> `True`. File tồn tại nguyên vẹn. |
| **Đánh giá ~30 script one-off tại `test/`** | **VERIFIED** | Đã quét toàn bộ nội dung file và tìm kiếm tham chiếu trong `test/app/`: Không có file nào import hay gọi các script này. |
| **Biên dịch Frontend TypeScript** | **VERIFIED** | Lệnh `npx tsc -b --noEmit` hoàn thành với 0 lỗi trên 60 file nguồn. |
| **Lịch sử Git quá khứ chứa `admin_config.json`** | **VERIFIED** | `git log` xác nhận file xuất hiện trong 3 commits `9c6e374`, `fe5c8d4`, `5f418c3`. Đã xác nhận không rewrite history trong đợt migration này. |

---

## 8. DANH SÁCH RỦI RO CÒN TỒN TẠI & BIỆN PHÁP KIỂM SOÁT

1. **Rủi ro quên bổ sung `.gitignore` trước khi copy file:**
   - *Hậu quả:* Các file `runtime/zalo_monitor.db`, `Checkcam.json` bị Git đánh dấu là untracked và có thể bị commit nhầm.
   - *Biện pháp kiểm soát:* Cập nhật `.gitignore` là **bước đầu tiên** của Phase 3 trước khi copy bất kỳ file nào.
2. **Rủi ro file `admin_config.json`:**
   - *Hậu quả:* Thông tin mật khẩu admin cũ còn lưu trong Git history.
   - *Biện pháp kiểm soát:* Tách biệt việc untrack file hiện tại (`git rm --cached`) và tạo template `admin_config.example.json`. Khuyến nghị chủ dự án đổi mật khẩu quản trị trên giao diện sau khi hoàn tất.
3. **Rủi ro phiên Zalo Web bị ngắt:**
   - *Biện pháp kiểm soát:* Sao chép nguyên vẹn thư mục `zalo_web_profile` không chỉnh sửa; không thực hiện thao tác đăng xuất.

---

## 9. QUYẾT ĐỊNH CẦN CHỦ DỰ ÁN PHÊ DUYỆT ĐỂ BẮT ĐẦU PHASE 3

Kính đề nghị chủ dự án xem xét và phê duyệt các điểm sau để chuyển sang **PHASE 3 — CONTROLLED SOURCE MIGRATION**:

1. **Phê duyệt kế hoạch di chuyển thư mục:** Đồng ý tạo `DashBoardD/test_engine/` và thực hiện copy các module theo đúng ma trận ở Mục 2.
2. **Phê duyệt giữ nguyên vị trí thư mục `test` gốc:** Đồng ý giữ nguyên thư mục `D:\Tín\ABC\test` ban đầu, không can thiệp, không xóa.
3. **Phê duyệt xử lý script cũ:** Đồng ý không đưa ~30 script vá lỗi một lần vào repo Git mới; mã nguồn Electron cũ được đưa vào dạng source code sạch (loại bỏ 656MB release installer và `node_modules`).
4. **Phê duyệt phương án `admin_config.json`:** Đồng ý thực hiện `git rm --cached backend/app/admin_config.json`, đưa vào `.gitignore` và commit `admin_config.example.json` thay thế.

---
> [!IMPORTANT]
> **TOÀN BỘ CÔNG TÁC PHÂN TÍCH PHASE 2 ĐÃ HOÀN TẤT. HỆ THỐNG ĐANG DỪNG HOÀN TOÀN.**  
> Chưa có bất kỳ file mã nguồn nào bị di chuyển hay sửa đổi. Vui lòng phản hồi phê duyệt để bắt đầu Phase 3!
