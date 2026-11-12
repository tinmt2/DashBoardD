# BÁO CÁO KIỂM TOÁN LỊCH SỬ GIT & KẾ HOẠCH LÀM SẠCH BẢO MẬT (PHASE 6C)
**Dự án:** DashBoardD Monorepo (DashBoardD + Test Engine)  
**Địa điểm thực hiện:** `D:\Tín\ABC\DashBoardD`  
**Vai trò:** Senior Git Security Engineer  
**Thời gian kiểm toán:** 12/11/2026  
**Trạng thái kiểm toán:** `AUDIT COMPLETE — AWAITING APPROVAL`

---

## 1. TỔNG QUAN VÀ BỐI CẢNH KIỂM TOÁN

Sau khi hoàn tất thành công **Phase 6B (Controlled Admin Credential Rotation)**:
- Mật khẩu Admin đã được đổi sang mật khẩu mới do người dùng trực tiếp nhập, hash SHA-256 mới đã kích hoạt trên server live.
- Mật khẩu cũ và các session token cũ đã bị vô hiệu hóa hoàn toàn (trả về HTTP 401 khi xác thực).
- Chuỗi mật khẩu cũ trong quá khứ đã chính thức trở thành **dead credential**.

Tuy nhiên, trong quá khứ phát triển dự án, file cấu hình nhạy cảm `backend/app/admin_config.json` (chứa username, hash mật khẩu cũ, và `totp_secret` của crawler Inside) đã từng được commit và push lên repository từ xa trên GitHub (`https://github.com/tinmt2/DashBoardD.git`).

Mục tiêu của **Phase 6C** là thực hiện kiểm toán chỉ đọc (read-only audit) trên toàn bộ lịch sử Git, định vị chính xác phạm vi ảnh hưởng, so sánh các phương án xử lý, và xây dựng một quy trình kỹ thuật hoàn chỉnh để làm sạch lịch sử Git an toàn tuyệt đối mà không gây mất mát bất kỳ file chưa commit nào trong working tree.

> [!IMPORTANT]
> **Cam kết an toàn tuyệt đối trong Phase 6C:**
> - KHÔNG thực hiện rewrite history, KHÔNG chạy `git filter-repo` hay `git filter-branch`.
> - KHÔNG chạy `git push --force`.
> - KHÔNG chạy `git reset --hard`, `git clean` hoặc làm mất mát working-tree changes (18 modified files và 31 untracked baseline files được bảo toàn 100%).
> - KHÔNG in lộ mật khẩu, hash, OTP hay TOTP secret ra báo cáo hay log.

---

## 2. KẾT QUẢ KIỂM TOÁN LỊCH SỬ GIT (AUDIT FINDINGS)

### 2.1. Cấu trúc References và Remotes
Qua kiểm tra toàn bộ refs (`git show-ref`, `git branch -a`, `git tag -l`, `git stash list`):
- **Local Branches:** Chỉ có 01 nhánh duy nhất: `refs/heads/main` (HEAD trỏ tới `ab13c1d`).
- **Remote Branches:** Chỉ có 01 nhánh duy nhất: `refs/remotes/origin/main` (trỏ tới `ab13c1d`).
- **Remote URL:** `origin` -> `https://github.com/tinmt2/DashBoardD.git`.
- **Tags:** 0 tag (hoàn toàn không có tag nào cần rewrite).
- **Stashes:** 0 stash.
- **Trạng thái đồng bộ:** Nhánh `main` cục bộ đang ngang bằng (in sync) hoàn toàn với `origin/main`.

### 2.2. Định vị file nhạy cảm trong lịch sử Commit
Kiểm tra toàn bộ lịch sử Git đối với file `backend/app/admin_config.json`:
- **Tổng số commit trong toàn bộ repository:** 35 commit (từ commit khởi tạo `e31190c` ngày 10/10/2026 đến `ab13c1d` ngày 07/11/2026).
- **Số commit thực sự chứa hoặc sửa đổi `backend/app/admin_config.json`:** Chính xác **03 commit**:
  1. `9c6e374` (20/10/2026 10:31:59 +0700): `feat: integrate shared Employee database and API, fix FPT sync date format` — **[Thêm mới file]**
  2. `fe5c8d4` (24/10/2026 12:02:35 +0700): `fix: resolve 7-hour timezone offset for sync notifications and streamline notification UI` — **[Sửa đổi file]**
  3. `5f418c3` (26/10/2026 10:35:47 +0700): `fix: make auto-sync toggle instant-save and add 15m/30m quick select pills to prevent jumpback` — **[Sửa đổi file]**

### 2.3. Rà soát mở rộng các mẫu bí mật khác trong Git History
Đã quét toàn bộ commit tree với các mẫu đường dẫn nhạy cảm: `*secret*`, `*credential*`, `*.env*`, `*token*`, `*password*`:
- Chỉ có 01 kết quả trùng khớp: `dashboard-app/src/styles/lucian-tokens.css` (đây là file định nghĩa Design Tokens cho CSS giao diện người dùng, hoàn toàn không chứa bí mật bảo mật).
- Không có bất kỳ file `.env`, file private key (`.pem`, `.key`), file service account Google Cloud hay file session Zalo nào từng bị commit vào Git history của `DashBoardD`.

### 2.4. Phạm vi commit bị tác động nếu viết lại lịch sử
- **11 commit đầu tiên** (từ `e31190c` đến `50d75a4`): Hoàn toàn sạch, không chứa file nhạy cảm.
- **24 commit kế tiếp** (từ `9c6e374` đến `ab13c1d`): Là các commit downstream bắt đầu từ điểm phát sinh file `backend/app/admin_config.json`. Nếu thực hiện thanh lọc file này khỏi lịch sử, SHA-1 hash của toàn bộ **24 commit** này sẽ thay đổi.

---

## 3. PHÂN TÍCH VÀ ĐỐI CHIẾU CÁC PHƯƠNG ÁN XỬ LÝ

| Tiêu chí | Phương án 1: Giữ nguyên lịch sử (Status Quo) | Phương án 2: Làm sạch lịch sử bằng `git-filter-repo` (Đề xuất) |
| :--- | :--- | :--- |
| **Bản chất kỹ thuật** | Giữ nguyên 35 commit trên GitHub, chấp nhận `admin_config.json` tồn tại trong lịch sử 3 commit cũ. | Loại bỏ vĩnh viễn file `backend/app/admin_config.json` khỏi toàn bộ tree của 35 commit, tạo lịch sử sạch. |
| **Mức độ an toàn mật khẩu Admin** | **AN TOÀN**: Mật khẩu Admin đã được xoay vòng tại Phase 6B, mật khẩu cũ trong lịch sử là chuỗi vô giá trị (Dead Secret). | **RẤT CAO**: Không còn bất kỳ dấu vết nào của mật khẩu cũ lẫn cấu trúc config trong Git history. |
| **Mức độ an toàn TOTP Secret (Inside)** | **TRUNG BÌNH**: `totp_secret` (khóa Authenticator của Inside FPT) vẫn còn lưu trong commit `9c6e374..5f418c3`. Nếu repo bị public, crawler secret này có nguy cơ bị lộ. | **RẤT CAO**: Khóa TOTP Inside hoàn toàn biến mất khỏi commit history trên GitHub. |
| **Ảnh hưởng đến Commit Hash** | Không đổi (Zero impact). | 24 commit (từ `9c6e374` đến `HEAD`) sẽ đổi SHA hash. 11 commit đầu giữ nguyên. |
| **Yêu cầu Force Push lên GitHub** | **Không** cần force-push. | **Bắt buộc** phải `git push origin main --force`. |
| **Ảnh hưởng đến Collaborator / Máy khác** | Không ảnh hưởng. Các bản clone khác vẫn pull bình thường. | Bắt buộc các máy khác hoặc bản clone cũ phải re-clone hoặc `git reset --hard origin/main`. |
| **Rủi ro working-tree uncommitted** | Không có rủi ro. | Nếu không cách ly working tree cẩn thận, lệnh filter có thể tác động đến file chưa commit. |
| **Khuyến nghị áp dụng** | Phù hợp nếu repository vĩnh viễn là **Private Repository** nội bộ 1 người dùng. | **KHUYẾN NGHỊ**: Chuẩn hóa chuẩn mực bảo mật doanh nghiệp, loại bỏ triệt để mọi rủi ro rò rỉ credential. |

---

## 4. ĐÁNH GIÁ CHUYÊN SÂU VỀ RỦI RO CREDENTIAL

1. **Admin Password Hash:**
   - Trong 3 commit lịch sử, giá trị được lưu là SHA-256 hash của mật khẩu cũ.
   - Do Phase 6B đã cập nhật hash mật khẩu mới vào `backend/app/admin_config.json` cục bộ và đã kiểm thử thành công (server từ chối mật khẩu cũ), hash trong commit history không thể dùng để đăng nhập vào DashBoardD hiện tại.
2. **Inside TOTP Secret (`totp_secret`):**
   - Đây là secret dùng để sinh mã xác thực 2FA khi crawler đăng nhập vào hệ thống FPT Shop (`calllog.fptshop.com.vn`).
   - Vì secret này gắn liền với tài khoản Inside doanh nghiệp, việc lưu trữ nó trong commit history trên remote repository tiềm ẩn rủi ro nếu quyền truy cập repo bị chia sẻ ngoài ý muốn.
   - **Kết luận:** Phương án 2 (History Rewrite) mang lại giá trị bảo mật thực chất lớn nhất chính là triệt tiêu vĩnh viễn sự tồn tại của `totp_secret` trên GitHub.

---

## 5. QUY TRÌNH THỰC THI LÀM SẠCH AN TOÀN (NẾU ĐƯỢC PHÊ DUYỆT)

Để đảm bảo **không bao giờ mất dữ liệu**, phương pháp được đề xuất là **Isolate Working Clone**: không thao tác trực tiếp trên working tree đang có 18 modified files, mà thực hiện qua một bản clone trung gian sạch.

```
+-----------------------------------------------------------------------------------+
| BƯỚC 1: TẠO FULL BACKUP & BUNDLE AN TOÀN TUYỆT ĐỐI                                |
| - Tạo Git Bundle hoàn chỉnh: _backups_phase6c/DashBoardD_pre_rewrite.bundle        |
| - Nén toàn bộ working tree hiện tại: _backups_phase6c/DashBoardD_full_tree.7z      |
+-----------------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------------+
| BƯỚC 2: CÀI ĐẶT CÔNG CỤ CHUẨN                                                     |
| - py -3.12 -m pip install git-filter-repo                                         |
+-----------------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------------+
| BƯỚC 3: THỰC THI QUA BẢN CLONE CÁCH LY (CLEAN ISOLATED CLONE)                     |
| - Clone repo sang thư mục tạm: D:\Tín\ABC\_filter_scratch                         |
| - Tại scratch: git filter-repo --path backend/app/admin_config.json --invert-paths|
| - Kiểm tra log tại scratch: xác nhận file đã biến mất hoàn toàn                   |
+-----------------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------------+
| BƯỚC 4: ĐỒNG BỘ COMMIT TREE VỀ WORKING REPO MÀ KHÔNG ẢNH HƯỞNG WORKING TREE       |
| - Fetch commit tree đã filter từ scratch về D:\Tín\ABC\DashBoardD                 |
| - Cập nhật refs/heads/main trỏ về commit sạch mới                                 |
| - Cấu hình lại origin remote URL                                                  |
+-----------------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------------+
| BƯỚC 5: KIỂM TRA HẬU LÀM SẠCH & REGRESSION TESTING                                |
| - Kiểm tra git status --short (18 modified, 31 untracked giữ nguyên)              |
| - Chạy pytest backend (37 tests) và pytest test_engine (28 tests)                 |
+-----------------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------------+
| BƯỚC 6: FORCE-PUSH LÊN GITHUB CÓ KIỂM SOÁT                                        |
| - git push origin main --force                                                    |
+-----------------------------------------------------------------------------------+
```

---

## 6. KẾ HOẠCH BẢO TOÀN DỮ LIỆU VÀ QUY TRÌNH ROLLBACK

### 6.1. Phương án Sao lưu dự phòng (Pre-Remediation Backup)
Trước khi bất kỳ thao tác nào diễn ra, hệ thống sẽ tự động tạo thư mục `D:\Tín\ABC\_backups_phase6c\` chứa:
1. `DashBoardD_history_backup.bundle`: Chứa 100% commit object, refs và lịch sử hiện tại. Nếu có bất kỳ sự cố nào, bundle này có thể phục hồi lại repository trong 1 giây (`git fetch DashBoardD_history_backup.bundle main:main`).
2. `DashBoardD_working_tree_pre_filter.7z`: Nén toàn bộ mã nguồn, cấu hình, file uncommitted và untracked.
3. Bản sao lưu `.git/refs/heads/main` ghi nhận commit hash gốc `ab13c1d6febc7f2d8d05138f606eee25d890f9bf`.

### 6.2. Quy trình Rollback tức thì (Kịch bản sự cố)
Nếu sau khi rewrite commit hash có bất kỳ lỗi không mong muốn nào:
```bash
# 1. Khôi phục branch main về commit hash gốc
git reset --soft ab13c1d6febc7f2d8d05138f606eee25d890f9bf

# 2. Hoặc khôi phục toàn bộ từ Git Bundle
git fetch D:/Tín/ABC/_backups_phase6c/DashBoardD_history_backup.bundle main:main
```
Toàn bộ working tree và các file đang chỉnh sửa sẽ không bị ảnh hưởng.

---

## 7. TÁC ĐỘNG ĐẾN COLLABORATOR VÀ BẢN SAO KHÁC

Nếu thực hiện Phương án 2 (Force Push commit tree mới):
1. **Đối với người dùng hiện tại trên máy này:** Working tree được bảo toàn toàn vẹn nhờ phương thức Clean Isolated Clone.
2. **Đối với các máy khác hoặc bản clone cũ (nếu có ai từng clone repository):**
   - Lệnh `git pull` thông thường sẽ báo lỗi do lịch sử commit bị phân kỳ (diverged history).
   - Cách xử lý trên máy khác:
     ```bash
     # Tùy chọn A (Khuyến nghị cho máy khác): Clone mới vào thư mục sạch
     git clone https://github.com/tinmt2/DashBoardD.git

     # Tùy chọn B (Nếu có thay đổi local trên máy khác): Fetch và hard-reset
     git fetch origin
     git reset --hard origin/main
     ```
3. **Đối với GitHub:**
   - Commit history của repository `tinmt2/DashBoardD` sẽ giảm từ 35 commit xuống một đồ thị 35 commit sạch (24 commit mới có hash mới).
   - File `backend/app/admin_config.json` sẽ không còn tồn tại trong bất kỳ commit nào trên GitHub.

---

## 8. DANH MỤC ĐIỂM CHỐT CẦN PHÊ DUYỆT (APPROVAL CHECKLIST)

Người dùng cần xem xét và cho ý kiến về các điểm chốt sau:

- [ ] **Lựa chọn phương án:**
  - **Lựa chọn A (Khuyến nghị):** Tiến hành thực hiện **Phương án 2 (History Rewrite qua `git-filter-repo`)** để thanh lọc triệt để `admin_config.json` khỏi toàn bộ lịch sử Git và force-push lên GitHub.
  - **Lựa chọn B:** Chấp nhận **Phương án 1 (Status Quo)**, giữ nguyên lịch sử hiện tại vì mật khẩu Admin đã được đổi sang mật khẩu mới và session tokens cũ đã bị hủy.
- [ ] **Xác nhận quyền Force Push:**
  - Xác nhận rằng bạn là người sở hữu duy nhất của repository `tinmt2/DashBoardD` hoặc các thành viên khác trong nhóm (nếu có) sẵn sàng re-clone lại repository sau khi force-push.
- [ ] **Xác nhận không có commit nào khác đang được push đồng thời:**
  - Đảm bảo không có tiến trình hoặc máy tính nào khác đang push code lên nhánh `main` trong quá trình thực hiện.

---

## 9. TRẠNG THÁI KẾT LUẬN

```
======================================================================
         TRẠNG THÁI: AUDIT COMPLETE — AWAITING APPROVAL
======================================================================
- Kiểm toán chỉ đọc: HOÀN TẤT 100%.
- Định vị file nhạy cảm: CHÍNH XÁC 3 COMMITS (9c6e374, fe5c8d4, 5f418c3).
- Phương án kỹ thuật: ĐÃ THIẾT KẾ ĐẦY ĐỦ VỚI CƠ CHẾ BẢO VỆ DỮ LIỆU ZERO-LOSS.
- Lệnh can thiệp Git / Force-push: ĐÃ KHÓA, CHỜ LỆNH PHÊ DUYỆT CỦA NGƯỜI DÙNG.
======================================================================
```
