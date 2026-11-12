# BÁO CÁO KẾT QUẢ GIAI ĐOẠN 1 — BACKUP, BASELINE VÀ KIỂM KÊ BẢO MẬT
# PHASE 9.1 — BACKUP, BASELINE AND SECURITY INVENTORY REPORT

**Dự án:** Hợp nhất mã nguồn DashBoardD + Test Engine  
**Giai đoạn thực hiện:** Phase 1 — Backup, Baseline và Security Inventory  
**Ngày thực hiện:** 11/11/2026 (22:25 UTC+7)  
**Kỹ sư thực hiện:** AI Pair Programmer / Senior DevOps & Software Architect  
**Trạng thái hiện tại:** **HOÀN THÀNH PHASE 1 — DỪNG HOÀN TOÀN CHỜ PHÊ DUYỆT ĐỂ SANG PHASE 2**

---

## 1. EXECUTIVE SUMMARY (TÓM TẮT THỰC THI)

1. **Bảo toàn hiện trạng & Working Tree:**
   - Đã chụp và ghi nhận toàn bộ trạng thái Git baseline tại `DashBoardD`: Nhánh `main`, commit HEAD `ab13c1d`, **18 files modified** và **31 files untracked** được bảo toàn nguyên vẹn 100%. Không có bất kỳ lệnh ghi đè, xóa hoặc `git reset/clean` nào được thực thi.
2. **Khởi tạo và kiểm chứng bản sao lưu độc lập (Independent Backup):**
   - Đã tạo thành công thư mục sao lưu độc lập ngoài Git tại `D:\Tín\ABC\_backups_phase1\`.
   - Bao gồm 2 gói nén toàn diện:
     - `DashBoardD_working_tree.7z` (138 MiB — chứa 3.292 files, toàn bộ working tree, git metadata, modified/untracked code, docs).
     - `TestEngine_working_tree.7z` (646 MiB — chứa 7.347 files, toàn bộ mã nguồn `app/`, `tests/`, `scripts/`, `desktop/`, `runtime/`, database, driver).
     - Thư mục giải nén nhanh `critical_uncommitted/` lưu trữ bản sao vật lý các file cơ sở dữ liệu (`opsmonitor.db`, `zalo_monitor.db`), bí mật và mã nguồn mới.
   - **Xác minh khôi phục (Restore Verification):** Chạy kiểm tra tính toàn vẹn 7-Zip (`7z t`) đạt **100% OK**. Thực hiện giải nén thử nghiệm mẫu và đối soát mã băm SHA-256 (`admin_config.json`, `Checkcam.json`) cho kết quả **trùng khớp tuyệt đối (Match = True)**.
3. **Kiểm kê bảo mật (Security Inventory):**
   - **Phát hiện rủi ro cao:** `backend/app/admin_config.json` đang bị Git theo dõi và từng xuất hiện trong 3 commits lịch sử (`9c6e374`, `fe5c8d4`, `5f418c3`).
   - **Bảo mật Google Cloud:** `Checkcam.json` chứa Private Key RSA của Service Account `checkcam-bot@check-cam-485509.iam.gserviceaccount.com`, may mắn **chưa từng bị đưa vào Git**.
   - **Bảo mật phiên Zalo:** `test/runtime/zalo_web_profile` chứa phiên làm việc Zalo thật, nằm ngoài Git và đã được sao lưu an toàn.
   - Không in bất kỳ token, password, hash, private key hay TOTP secret nào ra báo cáo hay console.

---

## 2. ACTIONS PERFORMED (CÁC HÀNH ĐỘNG THỰC TẾ ĐÃ THỰC HIỆN)

| STT | Hành động thực hiện | Kết quả thực tế | Phân loại |
| :---: | :--- | :--- | :---: |
| 1 | Xác minh repo `DashBoardD` và thư mục `test` | Xác nhận `DashBoardD` là Git root duy nhất; `test` không có Git. | **VERIFIED** |
| 2 | Chụp ảnh trạng thái Git (Git Baseline Capture) | Ghi nhận commit `ab13c1d`, 18 modified, 31 untracked. | **VERIFIED** |
| 3 | Tạo thư mục backup độc lập `_backups_phase1` | Đã tạo tại `D:\Tín\ABC\_backups_phase1\`. | **VERIFIED** |
| 4 | Nén lưu trữ DashBoardD working tree | Tạo `DashBoardD_working_tree.7z` (138 MiB, 3.292 files). | **VERIFIED** |
| 5 | Nén lưu trữ Test Engine working tree | Tạo `TestEngine_working_tree.7z` (646 MiB, 7.347 files). | **VERIFIED** |
| 6 | Sao lưu mirror không nén các file nhạy cảm & DB | Lưu vào `_backups_phase1\critical_uncommitted\`. | **VERIFIED** |
| 7 | Sinh bảng mã băm SHA-256 toàn bộ backup | Bảng mã băm đã được tạo và ghi nhận. | **VERIFIED** |
| 8 | Kiểm chứng tính toàn vẹn archive (`7z t`) | Cả 2 file `.7z` đạt trạng thái `Everything is Ok`. | **VERIFIED** |
| 9 | Thử nghiệm khôi phục mẫu và so khớp hash | Giải nén sandbox, đối soát SHA-256: `Match = True`. | **VERIFIED** |
| 10 | Kiểm kê secrets trong git history và runtime | Phát hiện `admin_config.json` trong Git; `Checkcam.json` ngoài Git. | **VERIFIED** |

---

## 3. FILES CHANGED / CREATED (DANH SÁCH FILE ĐÃ TẠO / THAY ĐỔI)

Trong Phase 1, **tuyệt đối không chỉnh sửa hoặc xóa bất kỳ file mã nguồn hiện có nào**. Chỉ tạo các file backup và báo cáo:

1. **Thư mục sao lưu mới:**
   - `D:\Tín\ABC\_backups_phase1\DashBoardD_working_tree.7z` (143.692.055 bytes)
   - `D:\Tín\ABC\_backups_phase1\TestEngine_working_tree.7z` (676.814.343 bytes)
   - `D:\Tín\ABC\_backups_phase1\critical_uncommitted\` (Bản sao vật lý `opsmonitor.db`, `zalo_monitor.db`, `admin_config.json`, `Checkcam.json`, `config.json`, `token.txt`, untracked test routes & proxy).
2. **File tài liệu báo cáo mới:**
   - `D:\Tín\ABC\DashBoardD\docs\PHASE_9_1_BACKUP_SECURITY_REPORT.md` (Báo cáo hiện tại).

---

## 4. BACKUP STATUS & RESTORATION VERIFICATION

### A. Thông tin chi tiết các bản sao lưu
- **Vị trí lưu trữ:** `D:\Tín\ABC\_backups_phase1\` (Nằm ngoài phạm vi của repo `DashBoardD`).
- **Thời điểm hoàn thành:** 11/11/2026 22:24:00.
- **Dung lượng đĩa trống còn lại trên ổ D:** **12,48 GB Free** (Đảm bảo an toàn bộ nhớ đệm).

### B. Bảng mã băm SHA-256 kiểm chứng
| Tệp sao lưu / Tệp trọng yếu | Dung lượng | SHA-256 Checksum | Trạng thái |
| :--- | :---: | :--- | :---: |
| `DashBoardD_working_tree.7z` | 138 MiB | `EE5F1C5C851DAA360EF8ABB277C77750117C72E8223D9A83CF316B44E3B213CB` | **VERIFIED** |
| `TestEngine_working_tree.7z` | 646 MiB | `1A1AC7B5632166A695CE2C691EC9BD1FC1F8D7DD79DCB29E2B661821E58A4399` | **VERIFIED** |
| `opsmonitor.db` (Backup mirror) | 27.009.024 B | `6D6948DB74C80F1AB628C24D30AB53E6291843C4258FD3FE542C3EB328AE5E9E` | **VERIFIED** |
| `zalo_monitor.db` (Backup mirror) | 1.146.880 B | `429572647AE662C0C9393AA0172C25B4A07BB4A456C6CD38F140C29E30FD734D` | **VERIFIED** |
| `admin_config.json` (Backup mirror) | 189 B | `466CD4BCC92F77FDC7E17CC710C4605C62D16371BEEC7D61A19ECAD7C623E69E` | **VERIFIED** |
| `Checkcam.json` (Backup mirror) | 2.366 B | `CCFA759AB405736BD20D6AC121A686E82AD1A97A580F805FD6487F99CA44ED63` | **VERIFIED** |
| `config.json` (Backup mirror) | 1.382 B | `F96A0DE204A06106A6F1D11A5EFE0B657B1CB8754117B9884DDC5CBA16773EB2` | **VERIFIED** |

### C. Kết quả thử nghiệm phục hồi (Restoration Test)
- **Kiểm tra khối dữ liệu nén (`7z t`):**
  - `DashBoardD_working_tree.7z`: 523 folders, 3.292 files, 307.296.983 bytes uncompressed -> **PASS (Everything is Ok)**.
  - `TestEngine_working_tree.7z`: 993 folders, 7.347 files, 2.017.671.852 bytes uncompressed -> **PASS (Everything is Ok)**.
- **Thử nghiệm khôi phục thực tế ra thư mục Sandbox:**
  - Trích xuất `admin_config.json` từ `DashBoardD_working_tree.7z`: Hash gốc khớp 100% với hash phục hồi (`Match = True`).
  - Trích xuất `Checkcam.json` từ `TestEngine_working_tree.7z`: Hash gốc khớp 100% với hash phục hồi (`Match = True`).
  - Thư mục sandbox đã được dọn dẹp sạch sẽ sau kiểm thử.

---

## 5. BÁO CÁO KIỂM KÊ BẢO MẬT (SECURITY INVENTORY & RISK ASSESSMENT)

> [!IMPORTANT]
> Toàn bộ các giá trị mật mã, token, private key và chuỗi xác thực được che giấu tuân thủ nghiêm ngặt nguyên tắc bảo mật. Báo cáo chỉ định danh loại bí mật, vị trí và mức độ rủi ro.

| Hệ thống | Vị trí tệp | Loại bí mật / Dữ liệu nhạy cảm | Tình trạng Git | Mức độ rủi ro | Đánh giá & Khuyến nghị |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **Dashboard Admin** | `backend/app/admin_config.json` | - Hash mật khẩu Admin<br>- TOTP Secret (Base32)<br>- Active Session Tokens | **ĐANG BỊ TRACK** (Có trong lịch sử commits `9c6e374`, `fe5c8d4`, `5f418c3`) | **CRITICAL** | **Nguy cơ cao nhất.** Bắt buộc gỡ bỏ tracking (`git rm --cached`) trong Phase 3, cập nhật `.gitignore` và tạo file mẫu `admin_config.example.json`. Cần đổi mật khẩu và reset TOTP Secret sau migration. |
| **Google Cloud Service Account** | `test/Checkcam.json`<br>`test/check-cam-485509-9a51b6797327.json` | - Private Key RSA của Service Account `checkcam-bot@check-cam-485509.iam.gserviceaccount.com`<br>- Quyền truy cập 2 Google Spreadsheets vận hành | **CHƯA TỪNG BỊ TRACK** (Không có trong Git) | **HIGH (Nếu bị commit)**<br>**SAFE (Hiện tại)** | May mắn chưa từng đưa lên Git vì thư mục `test` không có Git. Khi chuyển vào `DashBoardD/test_engine`, **tuyệt đối không được add vào Git**. Bổ sung quy tắc `*cred*.json` và `Checkcam.json` vào `.gitignore`. |
| **Zalo Web Automation** | `test/runtime/zalo_web_profile/` | - Phiên đăng nhập Zalo thật<br>- Cookies, LocalStorage, IndexedDB tài khoản giám sát | **CHƯA TỪNG BỊ TRACK** (Nằm trong thư mục ignored `runtime/`) | **HIGH (Nếu lộ session)**<br>**SAFE (Hiện tại)** | Phiên đăng nhập đang hoạt động bình thường. Đảm bảo toàn bộ thư mục `test_engine/runtime/` được cho vào `.gitignore`. Không đăng xuất hay xóa session gốc. |
| **Ticket SSC Automation** | `test/runtime/token.txt` | - Bearer Authorization Token (JWT 613 chars) dùng tự động hóa Ticket | **CHƯA TỪNG BỊ TRACK** | **MEDIUM** | Là token động do bot tự sinh trong phiên runtime. Được bảo vệ trong thư mục `runtime/`. |
| **Biến môi trường (.env)** | `test/.env` | - Biến `PYTHONPATH` | **CHƯA TỪNG BỊ TRACK** | **LOW** | Chỉ chứa định nghĩa đường dẫn Python cục bộ, không chứa secret nào. `DashBoardD/.env` không tồn tại. |
| **Cơ sở dữ liệu Vận hành** | `DashBoardD/backend/opsmonitor.db`<br>`test/runtime/zalo_monitor.db` | - Dữ liệu lịch sử 18.000+ sự vụ FPT Shop, Long Châu, Vaccine<br>- 677+ tin nhắn Zalo phản ánh sự cố | **CHƯA TỪNG BỊ TRACK** (Đã nằm trong `*.db` gitignore) | **MEDIUM** | Dữ liệu nội bộ vận hành. Cần đảm bảo `*.db` và `runtime/` luôn được gitignore chặt chẽ. |

---

## 6. DANH SÁCH DỊCH VỤ BÊN NGOÀI CẦN CHỦ DỰ ÁN XÁC NHẬN

1. **Google Cloud Platform (Dự án `check-cam-485509`):**
   - **Tài nguyên:** Service Account `checkcam-bot@check-cam-485509.iam.gserviceaccount.com`.
   - **Mục đích sử dụng:** Đọc/ghi các trang tính Google Sheets (`Cam mkn`, `Tổng camera`, `Gs An Ninh`, `Zalo_Bao_Cao_Ca`).
   - **Khuyến nghị:** Vì file `Checkcam.json` chưa từng bị đưa lên GitHub, Private Key này vẫn an toàn tại máy cục bộ. Khi đưa vào `DashBoardD`, key này sẽ được giữ cục bộ và gitignore. Nếu trong tương lai chủ dự án có ý định đưa repository lên GitHub công khai (Public), chủ dự án nên chủ động truy cập `console.cloud.google.com/iam-admin/serviceaccounts` để xoay vòng (Rotate Key).
2. **Tài khoản Quản trị Admin Dashboard:**
   - **Khuyến nghị:** Sau khi hoàn tất việc untrack `admin_config.json` khỏi Git ở các phase tiếp theo, chủ dự án nên đăng nhập vào trang `#/admin/system` để đổi mật khẩu và quét lại mã QR TOTP mới.
3. **Tài khoản Zalo Web Giám sát:**
   - Phiên đăng nhập trong `zalo_web_profile` vẫn hoàn toàn nguyên vẹn và đang hoạt động. Không cần thao tác gì từ chủ dự án ở bước này.

---

## 7. REMAINING RISKS & OBSERVATIONS (RỦI RO CÒN TỒN TẠI)

1. **Lịch sử Git quá khứ (Git History):** `admin_config.json` đã nằm trong các commit cũ trên GitHub (`origin/main`). Theo đúng nguyên tắc của Phase 1, chúng ta **không tự ý sửa lịch sử Git** (chưa dùng filter-repo hay force-push) để tránh gây hỏng nhánh của người dùng. Việc này sẽ được lập kế hoạch làm sạch riêng nếu chủ dự án yêu cầu sau khi hoàn thành migration code.
2. **Working Tree của DashBoardD:** Vẫn đang ở trạng thái có 18 modified files và 31 untracked files (đã được sao lưu đầy đủ và an toàn vào `_backups_phase1`). Chúng sẽ được giữ nguyên vẹn trong suốt quá trình triển khai.

---

## 8. APPROVAL REQUIRED FROM PROJECT OWNER (CÁC QUYẾT ĐỊNH CẦN PHÊ DUYỆT)

Để tiếp tục sang **PHASE 2 — PRE-MIGRATION TECHNICAL VALIDATION**, xin chủ dự án xem xét và phê duyệt:

1. **Xác nhận trạng thái Backup:** Xác nhận bản sao lưu tại `D:\Tín\ABC\_backups_phase1\` đã đầy đủ và đạt yêu cầu bảo vệ dữ liệu.
2. **Kế hoạch xử lý `admin_config.json`:** Đồng ý ở Phase 3 sẽ gỡ bỏ theo dõi file này khỏi Git bằng `git rm --cached`, thay thế bằng file mẫu `admin_config.example.json` và bổ sung vào `.gitignore`.
3. **Phê duyệt chuyển tiếp:** Cho phép chuyển sang **Phase 2 (Pre-Migration Technical Validation)** để rà soát chi tiết các đường dẫn, launcher, phân loại script cũ và lập kế hoạch di chuyển tối thiểu.

---

## 9. NEXT PHASE PROPOSAL (KẾ HOẠCH PHASE 2 DỰ KIẾN)

- **Mục tiêu Phase 2:** Kiểm tra kỹ thuật tiền di chuyển (Pre-Migration Technical Validation).
- **Các việc sẽ làm trong Phase 2 (khi được duyệt):**
  1. Rà soát toàn bộ các tham chiếu đường dẫn đến `D:\Tín\ABC\test` trong `unified_launcher.py`, `start_all.cmd` và các script khởi động.
  2. Phân loại danh sách cụ thể từng script trong thư mục `test/` (đang dùng, dev tool, legacy patch, scratch).
  3. Xác định quy cách xử lý file Excel ngoài dự án `D:/Tín/Lưu file LC/Danh sách vùng.xlsx`.
  4. Lập bản kế hoạch di chuyển chi tiết từng file `PHASE_9_2_PRE_MIGRATION_PLAN.md`.
  5. **Dừng lại xin phê duyệt trước khi di chuyển bất kỳ file nào.**

---
> [!IMPORTANT]
> **HỆ THỐNG ĐÃ HOÀN THÀNH TOÀN BỘ NHIỆM VỤ PHASE 1 VÀ ĐANG DỪNG HOÀN TOÀN.**  
> Vui lòng phản hồi xác nhận để phê duyệt Phase 2 khi bạn đã sẵn sàng!
