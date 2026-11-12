# BÁO CÁO XÁC MINH RUNTIME VÀ KHỞI ĐỘNG LẠI TEST ENGINE AN TOÀN
## PHASE 8.1H — SAFE WIN32 DESKTOP FIX & TEST ENGINE RELOAD REPORT

- **Thời gian thực hiện:** 11/11/2026
- **Trạng thái:** HOÀN THÀNH 100% — TẤT CẢ KỊCH BẢN ĐẠT PASS
- **Phạm vi kiểm thử:** Nghiệm thu runtime thực tế chức năng kích hoạt, khôi phục cửa sổ Zalo Web (Chrome App Mode) sau khi nạp code mới vào Test Engine Backend cổng 18020.
- **Hệ thống liên quan:**
  - Test Engine Backend: `test/` (Port 18020)
  - DashBoardD Backend: `DashBoardD/backend/` (Port 8000 — Giữ nguyên)
  - Frontend Dev Server: `http://localhost:5174` (Port 5174 — Giữ nguyên)
  - Profile Zalo: `D:\Tín\ABC\test\runtime\zalo_web_profile`

---

## 1. SOURCE FILE ĐÃ SỬA VÀ LÝ DO

| STT | File đã sửa | Thay đổi chính | Lý do kỹ thuật |
|:---:|:---|:---|:---|
| **1** | `test/app/services/window_activator.py` | Áp dụng luồng xử lý chuyên dụng (`threading.Thread`), mở Desktop có quyền (`DESKTOP_READOBJECTS \| DESKTOP_WRITEOBJECTS \| DESKTOP_ENUMERATE`), gán `SetThreadDesktop` trên luồng riêng, khôi phục và kích hoạt cửa sổ bằng Win32 chuẩn, đóng handle trong `finally`. | Loại bỏ rủi ro gán Desktop trên luồng dùng chung của FastAPI; tuân thủ nghiêm ngặt nguyên tắc Win32 không đổi desktop khi luồng đã có cửa sổ/hook; bảo đảm không rò rỉ handle; loại bỏ thao tác mô phỏng phím Alt tổng quát. |
| **2** | `test/tests/unit/test_window_activator.py` | Bổ sung 4 unit test: lỗi `OpenDesktopW`, lỗi `SetThreadDesktop`, xác nhận đóng handle `CloseDesktop`, và trường hợp không cấp tiêu điểm (`focus_refused`). | Đáp ứng đầy đủ yêu cầu kiểm thử biên (boundary test) và an toàn Win32 API. |

---

## 2. THÔNG TIN KHỞI ĐỘNG LẠI BACKEND CỔNG 18020

### 2.1. Tiến trình cũ và mới
- **PID Backend cũ:** `17676`
  - Thời gian khởi động: 18:07:52
  - Trạng thái trước khi dừng: `is_monitoring: False`, không có tác vụ chạy ngầm.
  - Phương thức dừng: Dừng có kiểm soát tiến trình đơn lẻ `Stop-Process -Id 17676 -Force`.
  - Xác nhận sau dừng: Cổng 18020 được giải phóng hoàn toàn; Dashboard 8000 và Vite 5174 không bị ảnh hưởng.
- **PID Backend mới:** `26640`
  - Thời gian khởi động: 19:43:45
  - CWD: `D:\Tín\ABC\test`
  - Command khởi chạy (xác minh từ `unified_launcher.py`):
    `C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe -m uvicorn app.api.main:app --host 127.0.0.1 --port 18020 --no-access-log`
  - Trạng thái startup:
    ```
    INFO: Started server process [26640]
    INFO: Waiting for application startup.
    INFO: Application startup complete.
    INFO: Uvicorn running on http://127.0.0.1:18020
    ```

### 2.2. Bằng chứng Backend thực sự nạp source code mới
- **Endpoint Health:** `GET http://127.0.0.1:18020/health` → Status 200:
  `{"success": true, "status": "ok", "service": "test-python-backend"}`
- **Endpoint `POST /open-browser`:** Trả về đối tượng `data` có cấu trúc hoàn chỉnh từ code mới:
  ```json
  {
    "success": true,
    "status": "ok",
    "service": null,
    "data": {
      "success": true,
      "activated": true,
      "action": "restored",
      "message": "Cửa sổ Zalo đã được khôi phục hiển thị trên màn hình.",
      "hwnd": 2756720
    },
    "message": "Cửa sổ Zalo đã được khôi phục hiển thị trên màn hình."
  }
  ```
  *(Khác biệt hoàn toàn với response cũ trước đây là `"data": null`)*.

---

## 3. KẾT QUẢ NGHIỆM THU RUNTIME (ACCEPTANCE RESULTS)

| Kịch bản | Nội dung kiểm thử | Kết quả | Bằng chứng thực tế ghi nhận |
|:---:|:---|:---:|:---|
| **D.1** | `GET /health` trả về thành công | **PASS** | `http://127.0.0.1:18020/health` trả về HTTP 200, service `test-python-backend`. |
| **D.2** | Zalo status phản ánh đúng thực tế | **PASS** | `adapter_status`: `browser_open=true`, `is_headless=false`, `logged_in=true`, `current_url="https://chat.zalo.me/"`. |
| **D.3** | Mở Zalo ở chế độ Chrome App Mode | **PASS** | Chrome khởi chạy với PID `25588`, tham số `--app=https://chat.zalo.me`, không omnibox, không tabs thừa, response `mode="app"`. |
| **D.4** | Bấm **Hiện Zalo** khi Dashboard ở phía trước | **PASS** | API phản hồi `activated=true`, `action="restored"`, `hwnd=2756720`, đưa cửa sổ Zalo hiển thị trên màn hình. |
| **D.5** | Cửa sổ bị thu nhỏ được khôi phục | **PASS** | Đã thu nhỏ cửa sổ (`SW_MINIMIZE`), sau đó gọi `open-browser`, `IsIconic(hwnd)` chuyển từ `True` sang `False` (khôi phục thành công bằng `SW_RESTORE`). |
| **D.6** | Không kích hoạt nhầm cửa sổ Chrome khác | **PASS** | Trong 42 tiến trình Chrome của máy, chỉ duy nhất HWND `2756720` (PID 25588) được nhận diện và xử lý. |
| **D.7** | Bấm lặp lại không tạo phiên thừa | **PASS** | Gọi lặp lại `POST /open-browser` 4 lần, số lượng tiến trình Main Chrome Zalo vẫn duy nhất là 1 (`[25588]`). |
| **D.8** | Session đăng nhập được giữ nguyên | **PASS** | Cookie trong `zalo_web_profile` bảo toàn, tự động vào tài khoản `"Trung Tâm Gscmr Frt"`, không cần quét QR. |
| **D.9** | API và UI phản ánh chính xác kết quả | **PASS** | Giao diện hiển thị nút "Hiện Zalo" / "Thu ngầm", đồng bộ trạng thái tức thời qua `fetchStatus()`. |
| **D.10** | Chạy lại toàn bộ test suite | **PASS** | **14/14 test Test Engine PASS** (100%), **37/37 test DashBoardD PASS** (100%). |

---

## 4. CHI TIẾT TRẠNG THÁI ZALO TRƯỚC VÀ SAU KIỂM THỬ

| Thông số | Trước khởi động lại (Phase 8.1G) | Sau khi nạp code mới (Phase 8.1H) |
|:---|:---:|:---:|
| **Backend PID (Port 18020)** | 17676 | **26640** (Nạp source mới) |
| **Main Chrome PID** | 17800 | **25588** (Khởi chạy Chrome App Mode) |
| **Trạng thái Trình duyệt** | `browser_open: true` | `browser_open: true` |
| **Trạng thái Chế độ** | Cửa sổ thông thường | **Chrome App Mode (`--app=https://chat.zalo.me`)** |
| **Trạng thái Đăng nhập** | `logged_in: true` | **`logged_in: true` (Tự động phục hồi)** |
| **Cửa sổ đại diện (HWND)** | 3476718 (desktop sandbox cũ) | **2756720 (Đã khôi phục hiển thị)** |
| **Thống kê dữ liệu quét** | 677 tin quét / 553 đã sync | **677 tin quét / 553 đã sync (Bảo toàn 100%)** |

---

## 5. CÁC API WIN32 VÀ KẾT QUẢ GHI NHẬN
- `OpenDesktopW`: Thành công với quyền `DESKTOP_READOBJECTS | DESKTOP_WRITEOBJECTS | DESKTOP_ENUMERATE`.
- `SetThreadDesktop`: Thực thi thành công trên luồng worker chuyên dụng `ZaloWin32Activator` (không ảnh hưởng luồng FastAPI).
- `IsWindow`: Trả về `1` (cửa sổ hợp lệ).
- `ShowWindow(hwnd, SW_RESTORE)`: Khôi phục cửa sổ từ trạng thái thu nhỏ thành công.
- `AllowSetForegroundWindow`: Cấp quyền chuyển tiêu điểm thành công cho PID 25588.
- `CloseDesktop`: Đóng handle desktop thành công trong khối `finally`, không gây rò rỉ tài nguyên hệ điều hành.

---

## 6. XÁC NHẬN GIỚI HẠN AN TOÀN VÀ TÍNH TOÀN VẸN HỆ THỐNG

1. **Dashboard Backend (Port 8000):** Giữ nguyên liên tục, không bị khởi động lại (tiến trình PID 4868 hoạt động ổn định).
2. **Frontend Dev Server (Port 5174):** Giữ nguyên liên tục, hot reload mượt mà.
3. **Cơ sở dữ liệu & Cấu hình:**
   - `opsmonitor.db` (27,009,024 bytes) nguyên vẹn 100%.
   - `admin_config.json` (189 bytes) nguyên vẹn 100%.
   - `test/run.cmd` không bị chỉnh sửa.
4. **Production Bundle:** Thư mục `dist/` **hoàn toàn không bị build hoặc thay đổi** theo đúng chỉ thị của người dùng.
5. **Dữ liệu Zalo:** Không gửi tin nhắn thật, không đăng xuất, không xóa profile.

---

## 7. KẾT LUẬN

Tất cả các rào cản kỹ thuật của Phase 8.1G đã được khắc phục hoàn toàn và nghiệm thu runtime thành công 100%:
- Cơ chế quản lý cửa sổ Zalo bằng Chrome App Mode và Win32 Worker Thread hoạt động chính xác, an toàn, không có lỗi tiềm ẩn.
- Các kịch bản trước đây bị **BLOCKED** đã chuyển thành **PASS** có bằng chứng runtime thực tế.
- Hệ thống đã sẵn sàng phục vụ người dùng.
