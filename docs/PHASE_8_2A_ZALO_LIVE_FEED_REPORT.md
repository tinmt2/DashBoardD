# BÁO CÁO NGHIỆM THU PHASE 8.2A
# ZALO LIVE MESSAGE FEED & SAFE RUNTIME DIAGNOSIS

**Ngày thực hiện:** 11/11/2026  
**Môi trường:** Dev Mode (Vite Port 5174, DashBoardD Backend Port 8000, Test Engine Backend Port 18020)  
**Phạm vi áp dụng:** Frontend `DashBoardD/dashboard-app/src/pages/test/ZaloMonitorPage.tsx` & Chẩn đoán Win32 Runtime Desktop  

---

## 1. TỔNG QUAN KẾT QUẢ THỰC HIỆN

Phase 8.2A đã hoàn thành 100% mục tiêu mà **không làm gián đoạn hệ thống, không thay đổi database, không tạo mock API/dữ liệu giả, và tuyệt đối không chạy build/đóng gói theo đúng chỉ thị của người dùng**:

1. **Khắc phục triệt để khoảng trống giao diện:** Tích hợp thành công component **Live Message Feed** vào `#/admin/zalo`, chiếm trọn phần diện tích màu đen bị bỏ trống bên dưới log hệ thống như ghi nhận trong ảnh phản hồi của người dùng.
2. **Khai thác 100% dữ liệu thực:** Nạp trực tiếp 50 tin nhắn mới nhất từ cơ sở dữ liệu SQLite thực tế `runtime/zalo_monitor.db` (hiện có 677 tin nhắn) thông qua API `GET /api/test/api/zalo/status?include_messages=true`.
3. **Bộ lọc & Trải nghiệm chuyên nghiệp:**
   - Hỗ trợ thanh tìm kiếm nội dung, người gửi, mã shop, loại sự cố.
   - Hỗ trợ 4 tab lọc nhanh: *Tất cả*, *Sự cố*, *Đã đẩy Sheet*, *Chờ xử lý*.
   - Hệ thống badge trực quan: Sự cố/Thông thường, Trạng thái phân tích AI, Trạng thái đồng bộ Google Sheets.
   - Hiển thị văn bản an toàn (chống XSS, `whitespace-pre-wrap`, cho phép bôi đen copy `select-text`, tuyệt đối không dùng `dangerouslySetInnerHTML`).
   - Có trạng thái Skeleton Loading khi tải, Empty State khi không tìm thấy kết quả, Error State kèm nút Thử lại.
   - Cơ chế phòng chống Race Condition và rò rỉ bộ nhớ (`isFetchingRef`, `isMountedRef`).
   - Tuân thủ tuyệt đối quy tắc **Purple Ban** (sử dụng palette màu Slate, Emerald, Amber, Sky, Rose; không dùng bất kỳ class tím/violet nào).
4. **Chẩn đoán pháp y chuyên sâu về cửa sổ Chrome Zalo (Section D):** Làm rõ nguyên nhân gốc rễ vì sao cửa sổ Zalo Web Chrome đã mở thành công ở backend nhưng không hiện lên desktop vật lý của người dùng, cùng quy trình chuyển giao an toàn (Transition Procedure) cho phase tiếp theo.

---

## 2. KIỂM TRA DỮ LIỆU & SCHEMA THỰC TẾ

| Tiêu chí | Kết quả xác minh thực tế |
| :--- | :--- |
| **Endpoint dữ liệu** | `GET /api/test/api/zalo/status?include_messages=true` (thông qua Reverse Proxy Port 8000 -> 18020) |
| **Tính chất Endpoint** | **100% GET Read-Only**, không ghi hay làm biến đổi trạng thái Zalo |
| **Nguồn lưu trữ** | SQLite database `D:\Tín\ABC\test\runtime\zalo_monitor.db`, bảng `zalo_messages` |
| **Tổng số bản ghi** | **677 tin nhắn thực tế** từ nhóm giám sát `GS AN NINH` |
| **Số lượng hiển thị** | 50 tin nhắn mới nhất (`ORDER BY id DESC LIMIT 50`) |

### Schema các trường dữ liệu:
- `id` (INTEGER): Định danh bản ghi
- `msg_hash` (TEXT): Khóa băm duy nhất của tin nhắn
- `group_name` (TEXT): Tên nhóm Zalo (`GS AN NINH`)
- `sender` (TEXT): Người gửi tin nhắn (ví dụ: `Tài`, `Minh Frt`, `Jezz`, `Tín`, ...)
- `raw_content` (TEXT): Nội dung nguyên bản tin nhắn báo cáo / sự vụ
- `detected_at` (TEXT): Thời gian hệ thống quét phát hiện tin
- `sent_at` (TEXT): Thời gian tin nhắn được gửi trên Zalo
- `is_error_candidate` (INTEGER / BOOLEAN): 1 = Sự cố lỗi, 0 = Tin thông thường
- `ai_status` (TEXT): `PENDING` / `SUCCESS` / `SKIPPED` / `FAILED`
- `ai_result` (DICT): Kết quả phân tích (Mã shop, loại sự cố, tóm tắt)
- `sheet_sync_status` (TEXT): `SYNCED` / `PENDING` / `FAILED`
- `sheet_synced_at` (TEXT): Thời điểm đồng bộ lên Google Sheets

---

## 3. CHI TIẾT THAY ĐỔI FRONTEND (ZaloMonitorPage.tsx)

### A. State & Concurrency Guard
- Khai báo interface chuẩn `ZaloMessage`.
- Thêm state `messages`, `isMessagesLoading`, `messagesError`, `lastUpdated`, `messageSearch`, `messageFilter`, `isManualRefreshing`.
- Áp dụng `isFetchingRef = useRef(false)` và `isMountedRef = useRef(true)` để tránh duplicate API requests khi polling hoặc khi người dùng click Refresh liên tục.
- `fetchStatus` được bọc trong `useCallback` nạp `getStatus(true)`, tự động cập nhật danh sách tin nhắn mỗi 10 giây (hoặc thủ công qua nút Làm mới).

### B. Bộ lọc thông minh (`filteredMessages`)
- Lọc theo Tab:
  - `Tất cả`: Xem toàn bộ 50 tin.
  - `Sự cố`: Chỉ xem tin có `is_error_candidate === 1`.
  - `Đã đẩy Sheet`: Chỉ xem tin có `sheet_sync_status === 'SYNCED'`.
  - `Chờ xử lý`: Chỉ xem tin có `sheet_sync_status === 'PENDING'`.
- Tìm kiếm tức thì (`messageSearch`): Tìm kiếm không phân biệt hoa thường trên cả `raw_content`, `sender`, `group_name`, `ai_result.store_code` và `ai_result.incident_type`.

### C. Giao diện Live Feed Card
- **Avatar & Người gửi:** Avatar tròn hiển thị ký tự đầu của người gửi, phân biệt màu giữa sự cố (Amber) và bình thường (Sky).
- **Hệ thống Badges:**
  - `Sự cố` (Icon AlertTriangle, nền amber-500/15) vs `Thông thường` (nền slate-800).
  - `AI đã duyệt` / `AI chờ` / `AI lỗi`.
  - `Đã đẩy Sheet` (kèm tooltip thời gian đồng bộ) / `Chờ đẩy Sheet` / `Lỗi Sheet`.
- **Khung nội dung tin nhắn:** Định dạng `whitespace-pre-wrap break-words font-mono text-xs text-slate-200 leading-relaxed bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/60 select-text`. Bổ sung class `select-text` giúp người dùng dễ dàng bôi đen copy nội dung báo cáo, số ticket, mã shop mà không bị ảnh hưởng bởi `select-none` của toàn trang.
- **Chi tiết AI:** Nếu tin nhắn đã qua phân tích AI, hiển thị thêm các pill nhỏ: `Mã shop: [Mã]` và `Loại lỗi: [Loại]`.

---

## 4. BÁO CÁO CHẨN ĐOÁN RUNTIME WINDOW (SECTION D)

### A. Hiện trạng thực tế tại máy chủ
- Khi khởi động Test Engine Backend (Port 18020) qua background task của Agent, tiến trình `python.exe` (PID 26640) được tạo ra bên trong phiên làm việc cô lập của môi trường thực thi (`exebox-TBGLVJ23W6D5OVFL7IOB2FYQ6D`).
- Tiến trình Selenium WebDriver khởi chạy Chrome (PID 25588) với tham số `--app=https://chat.zalo.me` kế thừa Desktop `exebox-...` này.
- Module `window_activator.py` tìm thấy đúng HWND `2756720`, khôi phục (`SW_RESTORE`) và đưa cửa sổ lên Foreground của Desktop `exebox-...`. Do đó, phía backend log ghi nhận hoàn toàn chính xác: `Cửa sổ Zalo đã được khôi phục hiển thị trên màn hình.`

### B. Vì sao người dùng không nhìn thấy cửa sổ trên màn hình vật lý?
1. **Kiến trúc bảo mật Windows NT Desktop Isolation:**
   - Màn hình người dùng đang nhìn thấy và tương tác thuộc Windows Station `WinSta0` và Desktop `Default`.
   - Các tiến trình tạo cửa sổ trên một Desktop khác (`exebox-...`) bị Windows ngăn chặn không cho hiển thị hoặc vẽ lên Desktop `Default` để đảm bảo cô lập tiến trình.
2. **Cơ chế tái sử dụng của Unified Launcher:**
   - Khi người dùng chạy `start_all.cmd` (Lựa chọn 1 - Dev Mode) từ màn hình console cá nhân trên desktop `Default`, script kiểm tra thấy Port 18020 đã đang mở và vượt qua Health Check:
     ```
     [+] Test Engine Backend (Port 18020): Đã đang chạy và hoạt động tốt (Tái sử dụng an toàn).
     ```
   - Do đó, launcher tái sử dụng tiến trình nền có sẵn thay vì khởi tạo tiến trình backend mới dưới tài khoản tương tác của người dùng trên Desktop `Default`.
   - Kết quả là: Giao diện web hiển thị đầy đủ dữ liệu (nhờ reverse proxy), nhưng lệnh mở/kích hoạt cửa sổ Chrome GUI lại được thực thi trên Desktop sandbox.

---

## 5. QUY TRÌNH CHUYỂN GIAO AN TOÀN (TRANSITION PROCEDURE CHO PHASE SAU)

Khi người dùng muốn cửa sổ Chrome Zalo xuất hiện trực tiếp trên màn hình vật lý (`Default`), quy trình an toàn không ảnh hưởng dữ liệu sẽ như sau:

1. **Bước 1 (Dừng tiến trình nền):** Người dùng cho phép dừng tác vụ nền Port 18020 của agent.
2. **Bước 2 (Khởi chạy từ màn hình vật lý):** Người dùng chạy `D:\Tín\ABC\start_all.cmd` -> Chọn `[1]` hoặc `[2]` trực tiếp từ cửa sổ Command Prompt / PowerShell của mình trên Desktop `Default`.
3. **Bước 3 (Xác nhận):** Launcher sẽ tự động khởi động Test Engine Backend trực tiếp dưới phiên tương tác người dùng (`WinSta0\Default`). Khi đó, nút **Hiện Zalo** / **Mở Zalo Web** sẽ kích hoạt cửa sổ Chrome Zalo nổi trực tiếp lên trước mắt người dùng.

---

## 6. KẾT QUẢ KIỂM THỬ & BẢO ĐẢM AN TOÀN

1. **Linting & Type Safety:**
   - `npx oxlint src/pages/test/ZaloMonitorPage.tsx`: **0 Errors**.
   - `npx tsc -b --noEmit`: **0 Errors, 0 Warnings**.
2. **Backend Unit Tests:**
   - `test/tests/unit/test_window_activator.py` & `test_zalo_app_mode_activation.py`: **14/14 passed** (100%).
   - `DashBoardD/backend/tests/`: **37/37 passed** (100%).
3. **Kiểm tra tính toàn vẹn dữ liệu (Integrity Check):**
   - `DashBoardD/backend/opsmonitor.db`: **27,009,024 bytes** (Nguyên vẹn).
   - `test/runtime/zalo_monitor.db`: **1,146,880 bytes** (Nguyên vẹn).
   - `DashBoardD/backend/app/admin_config.json`: **189 bytes** (Nguyên vẹn).
   - Thư mục `dashboard-app/dist/`: **Không bị can thiệp, không chạy build theo đúng lệnh đóng gói**.
