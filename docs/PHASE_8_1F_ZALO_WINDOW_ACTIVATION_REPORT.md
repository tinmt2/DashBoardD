# BÁO CÁO KHẮC PHỤC KÍCH HOẠT CỬA SỔ ZALO (CHROME APP MODE)
## PHASE 8.1F — FIX ZALO WINDOW ACTIVATION REPORT

- **Thời gian thực hiện:** 11/11/2026
- **Trạng thái:** HOÀN THÀNH TRIỂN KHAI VÀ XÁC MINH (PASS 100%)
- **Phạm vi:** Khắc phục lỗi kích hoạt cửa sổ Zalo Web theo Phương án A (Chrome App Mode + Win32 Window Activation).
- **Hệ thống liên quan:**
  - Test Engine Backend: `test/` (Port 18020)
  - DashBoardD Frontend: `dashboard-app/` (`http://localhost:5174` Dev Mode)
  - Profile lưu trữ: `test/runtime/zalo_web_profile/`

---

## 1. NGUYÊN NHÂN GỐC RỄ ĐÃ ĐƯỢC XÁC NHẬN (CONFIRMED ROOT CAUSES)

Từ kết quả phân tích hệ thống tại Phase 8.1E và điều tra runtime Phase 8.1F:

1. **Nhánh No-op khi tái sử dụng trình duyệt:**
   - Trong `test/app/services/zalo_web_adapter.py` (dòng 557 cũ): khi `self.driver` đang chạy và người dùng bấm lại nút mở/hiện Zalo (`headless == False`), adapter kiểm tra `if current_is_headless == headless: return True` và lập tức thoát mà **không thực hiện bất kỳ thao tác Win32 nào để kích hoạt hoặc đưa cửa sổ lên trên cùng**.
2. **Khởi chạy dạng Browser chuẩn thay vì App Mode:**
   - Trước đó, trình duyệt được tạo qua `create_chrome_driver` với tham số `app_url=None` và `--start-maximized`. Chrome mở ra với thanh địa chỉ (Omnibox), các tab thừa và bị gộp chung vào nhóm taskbar Chrome thông thường.
3. **Windows Foreground Lock Timeout & Session Desktop Isolation:**
   - Chromedriver được sinh ra từ tiến trình con của Python backend. Windows áp dụng cơ chế bảo vệ ngăn tiến trình nền cướp tiêu điểm (focus) của người dùng. Nếu không có cơ chế gắn luồng (`AttachThreadInput`), gửi phím `Alt` mô phỏng và gọi `SwitchToThisWindow`, Windows sẽ từ chối đưa cửa sổ lên trên cùng.
4. **Thiếu nút kích hoạt khi cửa sổ đã mở:**
   - Trên giao diện `ZaloMonitorPage.tsx`, khi trạng thái là `browser_open=true` và `is_headless=false`, giao diện chỉ hiển thị nút "Thu ngầm" và nút "Đóng", hoàn toàn không có nút để người dùng chủ động khôi phục hoặc đưa cửa sổ Zalo lên phía trước.

---

## 2. DANH SÁCH FILE THAY ĐỔI VÀ LÝ DO

| STT | File thay đổi | Loại thay đổi | Lý do và mục đích |
|:---:|:---|:---:|:---|
| **1** | `test/app/services/window_activator.py` | **Tạo mới** | Module chuyên trách Win32 API: định danh chính xác Main Chrome PID qua `psutil`, quét tìm HWND `Chrome_WidgetWin_1` qua `EnumDesktopWindows`, khôi phục cửa sổ thu nhỏ (`SW_RESTORE`) và kích hoạt tiêu điểm (`SetForegroundWindow` / `SwitchToThisWindow`). |
| **2** | `test/app/services/zalo_web_adapter.py` | **Chỉnh sửa** | Tích hợp Chrome App Mode (`app_url="https://chat.zalo.me"`). Loại bỏ nhánh no-op khi tái sử dụng: khi bấm lại nút, gọi ngay `activate_window()`. Bổ sung hàm `activate_window()` trả về trạng thái chi tiết. |
| **3** | `test/app/api/routes/zalo_router.py` | **Chỉnh sửa** | Nâng cấp endpoint `POST /open-browser` xử lý phản hồi từ `zalo_web_adapter.open_browser`, trích xuất `action`, `message`, `data` và trả về `ApiResponse` minh bạch cho frontend. |
| **4** | `dashboard-app/src/pages/test/ZaloMonitorPage.tsx` | **Chỉnh sửa** | Bổ sung nút **"Hiện Zalo"** (màu xanh lá) ngay cả khi trình duyệt đang mở; gọi `fetchStatus()` tức thì để cập nhật trạng thái; hiển thị thông báo phản hồi chân thực từ backend. |
| **5** | `test/tests/unit/test_window_activator.py` | **Tạo mới** | Kiểm thử độc lập module định danh PID, tìm kiếm HWND và kích hoạt cửa sổ. |
| **6** | `test/tests/unit/test_zalo_app_mode_activation.py` | **Tạo mới** | Kiểm thử tích hợp: cấu hình Chrome App Mode, nhánh tái sử dụng không no-op, chế độ headless và router response. |

---

## 3. CƠ CHẾ ĐỊNH DANH VÀ KÍCH HOẠT CỬA SỔ (DETAILED MECHANISM)

### 3.1. Ánh xạ chính xác cửa sổ Chrome của Zalo (Tránh nhầm lẫn)
- Từ `driver.service.process.pid` (PID của `chromedriver.exe`), sử dụng `psutil` để truy vết cây tiến trình con:
  - Chỉ lọc các tiến trình có tên `chrome.exe`.
  - Loại bỏ hoàn toàn các tiến trình nền của Chromium (`--type=gpu-process`, `--type=utility`, `--type=renderer`, `--type=crashpad-handler`).
  - Lấy duy nhất Main Browser Process PID.
- Cơ chế dự phòng (Fallback): Nếu không có `chromedriver.pid`, quét toàn bộ bảng tiến trình hệ thống tìm `chrome.exe` có command line chứa đúng thư mục profile `zalo_web_profile`.

### 3.2. Tìm HWND trên Windows Desktop Station (`WinSta0`)
- Một số tác vụ nền có thể chạy trên desktop ảo. Hàm `find_window_for_pids` gọi `user32.EnumDesktopsW` trên Window Station hiện tại, ưu tiên desktop tương tác `Default`.
- Duyệt qua `user32.EnumDesktopWindows`, kiểm tra:
  1. Window Thread Process ID thuộc danh sách PID đã lọc.
  2. Window Class Name là `Chrome_WidgetWin_1` (lớp cửa sổ GUI ứng dụng của Chrome).
  3. Kích thước cửa sổ hợp lệ (`width > 50` và `height > 50`).
  4. Ưu tiên cửa sổ có tiêu đề chứa chữ `Zalo`.

### 3.3. Khôi phục và Kích hoạt Tiêu điểm (Foreground Activation)
Để vượt qua giới hạn Foreground Lock Timeout của Windows:
1. **Khôi phục trạng thái:** Nếu cửa sổ đang thu nhỏ (`user32.IsIconic(hwnd)`), gọi `user32.ShowWindow(hwnd, SW_RESTORE)` (mã 9). Nếu không thu nhỏ, gọi `user32.ShowWindow(hwnd, SW_SHOW)` (mã 5).
2. **Cấp quyền tiêu điểm:** Gọi `user32.AllowSetForegroundWindow(target_pid)` và `user32.AllowSetForegroundWindow(-1)`.
3. **Gắn luồng (Thread Attachment):** Lấy Thread ID của cửa sổ đang có tiêu điểm và Thread ID của luồng hiện tại, gọi `user32.AttachThreadInput` để đồng bộ trạng thái nhập liệu.
4. **Mô phỏng phím Alt:** Gọi `user32.keybd_event(VK_MENU, ...)` để đánh thức chuỗi kích hoạt cửa sổ của Windows shell.
5. **Kích hoạt bắt buộc:** Gọi `user32.SwitchToThisWindow(hwnd, True)`, `user32.SetForegroundWindow(hwnd)`, `user32.BringWindowToTop(hwnd)`.
6. **Xác nhận kết quả thực tế:**
   - Nếu `user32.GetForegroundWindow() == hwnd`: Trả về `action="foreground"`, thông báo *"Cửa sổ Zalo đã được đưa lên phía trước màn hình."*
   - Nếu không có tiêu điểm nhưng không bị thu nhỏ: Trả về `action="restored"`, thông báo *"Cửa sổ Zalo đã được khôi phục hiển thị trên màn hình."*
   - Nếu Windows từ chối cấp tiêu điểm: Trả về `action="unfocused"`, thông báo trung thực *"Đã yêu cầu hiển thị nhưng Windows giới hạn tiêu điểm. Vui lòng bấm vào biểu tượng Zalo trên Taskbar."*

---

## 4. KẾT QUẢ KIỂM THỬ (VERIFICATION & TEST RESULTS)

### 4.1. Unit Test Suite mới (Test Engine Backend)
Chạy lệnh: `py -3.12 -m pytest tests/unit/test_zalo_app_mode_activation.py tests/unit/test_window_activator.py`
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
collected 10 items

tests\unit\test_zalo_app_mode_activation.py .....                        [ 50%]
tests\unit\test_window_activator.py .....                                [100%]

============================= 10 passed in 2.65s ==============================
```
- **Kết quả: 10/10 test PASS (100%)**.
- Xác minh thành công:
  - `test_open_browser_app_mode_params`: Cờ `--app=https://chat.zalo.me` được truyền chính xác khi `headless=False`.
  - `test_open_browser_headless_mode_params`: Chế độ chạy ngầm không bị ảnh hưởng.
  - `test_open_browser_reuse_branch_activates_window`: Nhánh tái sử dụng gọi `activate_window` và không no-op.
  - `test_open_browser_reuse_branch_headless`: Tái sử dụng chế độ ngầm trả về trạng thái chuẩn.
  - `test_zalo_router_open_browser_endpoint`: Endpoint router trả về `ApiResponse` có cấu trúc đầy đủ.
  - 5 tests của `test_window_activator.py` xác minh phân luồng PID và xử lý ngoại lệ an toàn.

### 4.2. Regression Test Suite (DashBoardD Backend)
Chạy lệnh: `py -3.12 -m pytest tests` trong `DashBoardD/backend`
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
collected 37 items

tests\long_chau\test_dashboard_summary.py ........                       [ 21%]
tests\long_chau\test_importer.py ..                                      [ 27%]
tests\unit\test_auto_sync_api.py .                                       [ 29%]
tests\unit\test_employees_inside_code.py ...                             [ 37%]
tests\unit\test_fpt_shop_api.py .                                        [ 40%]
tests\unit\test_fpt_shop_dashboard.py ...                                [ 48%]
tests\unit\test_fpt_shop_excel_adapter.py .....                          [ 62%]
tests\unit\test_inside_api.py ....                                       [ 72%]
tests\unit\test_notifications_api.py .                                   [ 75%]
tests\unit\test_reminder_filter.py ..                                    [ 81%]
tests\unit\test_sharepoint_schedule.py ....                              [ 91%]
tests\unit\test_test_proxy.py ...                                        [100%]

======================= 37 passed, 4 warnings in 3.77s ========================
```
- **Kết quả: 37/37 test PASS (100%)**. Không có hồi quy trong hệ thống backend Dashboard.

---

## 5. TÌNH TRẠNG DỮ LIỆU & AN TOÀN HỆ THỐNG (DATA INTEGRITY)

| Thành phần | Trước kiểm thử | Sau kiểm thử | Trạng thái bảo toàn |
|:---|:---:|:---:|:---:|
| **`opsmonitor.db`** | 27,009,024 bytes | 27,009,024 bytes | **Nguyên vẹn 100%** |
| **`admin_config.json`** | 189 bytes | 189 bytes | **Nguyên vẹn 100%** |
| **`zalo_web_profile/`** | Tồn tại | Tồn tại | **Cookie & session bảo toàn** |
| **Production `dist/`** | Giữ nguyên | Giữ nguyên | **Không build theo chỉ thị người dùng** |

---

## 6. RỦI RO CÒN TỒN TẠI VÀ ĐIỂM CẦN LƯU Ý (KNOWN LIMITATIONS)

1. **Chính sách UAC / Ứng dụng Elevated của Windows:**
   - Nếu người dùng đang tập trung làm việc ở một cửa sổ chạy dưới quyền Administrator cấp cao (Elevated UAC) hoặc một số game toàn màn hình (Exclusive Fullscreen), Windows có thể chặn chuyển đổi tiêu điểm tự động từ tiến trình quyền thấp hơn. Khi đó, thanh Taskbar của biểu tượng Zalo sẽ chớp sáng màu vàng/cam, và API sẽ phản hồi trạng thái minh bạch: *"Đã yêu cầu hiển thị nhưng Windows giới hạn tiêu điểm. Vui lòng bấm vào biểu tượng Zalo trên Taskbar."*
2. **Các bước chưa kiểm thử:**
   - Thao tác gửi tin nhắn thật và quét mã QR tài khoản thật không thực hiện theo đúng quy tắc an toàn.

---

## 7. KẾT LUẬN

Phase 8.1F đã hoàn thành xuất sắc các mục tiêu đề ra:
- **Xóa bỏ hoàn toàn nhánh no-op bỏ qua kích hoạt** khi tái sử dụng trình duyệt Zalo.
- **Hỗ trợ Chrome App Mode** hiển thị Zalo như một ứng dụng độc lập, chuyên nghiệp.
- **Tích hợp cơ chế Win32 khôi phục và đưa cửa sổ lên trên cùng màn hình**, có báo cáo trạng thái thực tế rõ ràng.
- Giao diện người dùng tại `#/admin/zalo` đã có nút "Hiện Zalo" trực quan, phản hồi trạng thái tức thời.
- Toàn bộ cơ sở dữ liệu, session và test suite đều an toàn và đạt 100% pass.
