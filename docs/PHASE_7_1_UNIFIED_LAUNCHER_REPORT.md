# BÁO CÁO NGHIỆM THU TRIỂN KHAI UNIFIED LAUNCHER (PHASE 7.1)
**Hệ thống:** DashBoardD & Test Application Engine  
**Thời gian thực hiện:** 11/11/2026  
**Trạng thái nghiệm thu:** **PASS (100% - ĐẠT YÊU CẦU AN TOÀN VẬN HÀNH)**

---

## 1. TỔNG QUAN & QUYẾT ĐỊNH ĐÃ THỰC THI

Căn cứ theo kế hoạch kỹ thuật đã được phê duyệt trong `PHASE_7_0_UNIFIED_LAUNCHER_PLAN.md`, giai đoạn **Phase 7.1** đã hoàn tất việc thiết kế, xây dựng và kiểm thử độc lập bộ công cụ khởi chạy hợp nhất (**Unified Launcher**) với các quyết định kiến trúc:

1. **Điểm nhập cảnh duy nhất (Root Entry Point):** Đặt tại `D:\Tín\ABC\start_all.cmd`, cho phép người dùng khởi chạy toàn bộ hệ thống bằng 1 cú click đúp chuột hoặc từ Command Prompt / PowerShell.
2. **Lõi điều phối trung tâm (Python Core Engine):** Đặt tại `D:\Tín\ABC\unified_launcher.py`, sử dụng **100% thư viện chuẩn (Standard Library)** của Python (`sys`, `os`, `subprocess`, `urllib.request`, `socket`, `shutil`, `signal`, `webbrowser`, `json`, `time`), không cài thêm bất kỳ gói npm hay pip ngoại lai nào.
3. **Menu tương tác thông minh (Interactive Menu & CLI):**
   - Lựa chọn `[1]`: Khởi chạy Chế độ Phát triển (Dev Mode: Port 5174, 8000, 18020)
   - Lựa chọn `[2]`: Khởi chạy Chế độ Vận hành (Production Mode: Port 8000, 18020)
   - Lựa chọn `[3]`: Kiểm tra trạng thái hệ thống (Read-only Status & Health Check)
   - Lựa chọn `[0]`: Thoát an toàn
   - Hỗ trợ tham số dòng lệnh trực tiếp: `--dev`, `--prod`, `--status`, `--help`.
4. **Cơ chế kiểm tra sức khỏe đa tầng (Non-Destructive Health Gate):**
   - Chỉ tự động mở trình duyệt (`webbrowser.open`) sau khi toàn bộ health check của các service bắt buộc đã phản hồi HTTP 200 OK (`http://127.0.0.1:8000/api/health` trả về `"ok"`, `http://127.0.0.1:18020/health` trả về `"test-python-backend"`, và Frontend trả về HTML hợp lệ).
5. **Chính sách an toàn tiến trình (Process Safety & Ownership Policy):**
   - **Tái sử dụng thông minh (Safe Reuse):** Nếu service đã đang chạy hợp lệ từ trước (ví dụ do dev khởi động thủ công), launcher tự động nhận diện và tái sử dụng, **không kill** và không khởi động trùng lặp.
   - **Xử lý xung đột cổng an toàn (Conflict Protection):** Nếu cổng bị chiếm dụng bởi tiến trình lạ không vượt qua health check, launcher cảnh báo chi tiết và dừng an toàn; **tuyệt đối không kill tiến trình lạ**.
   - **Dọn dẹp có kiểm soát (Clean Shutdown):** Launcher chỉ theo dõi các tiến trình được tạo ra trong phiên làm việc hiện tại (`SPAWNED_PROCESSES`). Khi nhận tín hiệu dừng (Ctrl+C hoặc lỗi), chỉ các PID này bị thu hồi; toàn bộ tiến trình hệ thống có từ trước được bảo toàn nguyên vẹn.
6. **Bảo toàn 100% tài nguyên:**
   - Giữ nguyên toàn bộ script cũ: `test/run.cmd`, `DashBoardD/start_dev.bat`, `start_server.bat`, `start_unified.bat`, `open_desktop_app.bat`.
   - Cơ sở dữ liệu `opsmonitor.db` và cấu hình `admin_config.json` giữ nguyên kích thước và checksum SHA256.

---

## 2. KIẾN TRÚC & CƠ CHẾ HOẠT ĐỘNG CỦA UNIFIED LAUNCHER

### 2.1. Wrapper Script: `D:\Tín\ABC\start_all.cmd`
- Nhận diện tự động môi trường Python trên máy tính Windows (`py -3.12` hoặc `python`).
- Chuyển tiếp toàn bộ tham số dòng lệnh (`%*`) sang `unified_launcher.py`.
- Tự động dừng hiển thị thông báo lỗi thân thiện nếu máy tính chưa cài đặt Python.

### 2.2. Core Engine: `D:\Tín\ABC\unified_launcher.py`
```
                    ┌─────────────────────────┐
                    │     start_all.cmd       │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   unified_launcher.py   │
                    └────────────┬────────────┘
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
  [Dev Mode (1)]          [Prod Mode (2)]        [Status Check (3)]
- Port 8000 (Backend)   - Port 8000 (Web+API)   - Audit Port 8000
- Port 18020 (Test)     - Port 18020 (Test)     - Audit Port 18020
- Port 5174 (Vite Dev)  - Kiểm tra dist/index   - Audit Port 5174
- Mở: localhost:5174    - Mở: localhost:8000    - Audit Dist Build
```

### 2.3. Ba trạng thái kiểm tra dịch vụ (`inspect_service`)
| Trạng thái | Điều kiện kỹ thuật | Hành vi của Launcher |
| :--- | :--- | :--- |
| **`FREE`** | Cổng TCP chưa có kết nối (`connect_ex != 0`) | Tiến hành tạo tiến trình con (`subprocess.Popen`), ghi nhận PID vào `SPAWNED_PROCESSES`, chờ health check. |
| **`RUNNING_VALID`** | Cổng TCP đang mở VÀ endpoint trả về HTTP 200 + snippet mong đợi | Ghi nhận `"Đã đang chạy và hoạt động tốt (Tái sử dụng an toàn)"`, không spawn thêm tiến trình, không kill tiến trình đang chạy. |
| **`CONFLICT_UNKNOWN`** | Cổng TCP đang mở NHƯNG health endpoint thất bại hoặc nội dung sai | Cảnh báo xung đột cổng, thông báo cho người dùng giải phóng cổng, dừng quy trình an toàn, **không kill tiến trình lạ**. |

---

## 3. KẾT QUẢ KIỂM THỬ THỰC TẾ (TEST MATRIX - 9/9 PASS)

Bộ kiểm thử thực tế `test/scratch/verify_launcher_logic.py` đã được thực thi độc lập với kết quả chi tiết như sau:

| STT | Tên bài kiểm thử | Lệnh / Cơ chế kiểm tra | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **1** | **Cú pháp CLI & Trợ giúp** | `start_all.cmd --help`<br>`start_all.cmd --bad-arg` | In hướng dẫn sử dụng (code 0).<br>Báo lỗi tham số không hợp lệ (code 1). | Trả về đúng hướng dẫn cú pháp và mã lỗi code 1 khi có cờ lạ. | **PASS** |
| **2** | **Kiểm tra trạng thái (Read-only)** | `start_all.cmd --status` | Liệt kê tình trạng Port 8000, 18020, 5174 mà không bật/tắt tiến trình. | Hiển thị trạng thái ONLINE của cả 4 endpoint và trạng thái `dist`. | **PASS** |
| **3** | **Logic phân loại dịch vụ** | Hàm `inspect_service` trên cổng 8000, 18020, 19999 và mock conflict. | Trả về chính xác 3 trạng thái: `RUNNING_VALID`, `FREE`, `CONFLICT_UNKNOWN`. | 8000: `RUNNING_VALID`<br>18020: `RUNNING_VALID`<br>19999: `FREE`<br>Mock: `CONFLICT_UNKNOWN`. | **PASS** |
| **4** | **Tái sử dụng dịch vụ an toàn** | Gọi `start_dashboard_backend()` và `start_test_backend()` khi dịch vụ đang chạy. | Nhận diện dịch vụ có sẵn, trả về True, không spawn thêm tiến trình trùng lặp. | Tái sử dụng thành công cả 2 backend, số lượng `SPAWNED_PROCESSES` tăng thêm là 0. | **PASS** |
| **5** | **Quyền sở hữu & Dọn dẹp có kiểm soát** | Spawn tiến trình giả lập (PID 10600), gọi `clean_shutdown()`. | Chỉ kill đúng PID 10600; các PID 20896, 23724, 11372 giữ nguyên. | PID 10600 đã bị dừng. Cả 3 cổng 8000, 18020, 5174 vẫn hoạt động bình thường! | **PASS** |
| **6** | **Tính toàn vẹn Database & Config** | Kiểm tra kích thước và mã băm SHA256 của `opsmonitor.db` & `admin_config.json`. | Kích thước đúng 27,009,024 bytes; mã băm không đổi. | `opsmonitor.db`:<br>27,009,024 bytes, SHA256 khớp 100%.<br>`admin_config.json`: SHA256 khớp 100%. | **PASS** |
| **7** | **Bảo toàn các script hiện có** | Kiểm tra sự tồn tại của `test/run.cmd`, `start_dev.bat`, `start_server.bat`, `start_unified.bat`, `open_desktop_app.bat`. | Tất cả các script cũ còn nguyên vẹn, không bị xóa hoặc ghi đè. | Toàn bộ 5 tệp script cũ tồn tại nguyên bản 100%. | **PASS** |
| **8** | **Chuyển tiếp lệnh Batch Wrapper** | `start_all.cmd --status` chạy từ Command Prompt / PowerShell. | Batch wrapper chuyển tiếp tham số trơn tru sang Python core engine. | Batch script chạy thành công, mã thoát 0, hiển thị đầy đủ thông tin. | **PASS** |
| **9** | **Phục vụ giao diện Production** | Kiểm tra `dist/index.html` và truy vấn HTTP GET tới `http://localhost:8000/`. | Port 8000 trả về mã 200 kèm nội dung HTML của frontend production. | Phản hồi HTTP 200 chứa thẻ `<html` thành công. | **PASS** |

---

## 4. ĐỐI SOÁT TÍNH TOÀN VẸN CƠ SỞ DỮ LIỆU VÀ CẤU HÌNH

| Tài nguyên | Chỉ số trước Phase 7.1 | Chỉ số sau Phase 7.1 | Đánh giá |
| :--- | :--- | :--- | :---: |
| **`opsmonitor.db` Size** | 27,009,024 bytes | 27,009,024 bytes | **BẢO TOÀN** |
| **`opsmonitor.db` SHA256** | `73dec3d0536ecf1c327be9b140b06a68fc99e4a316c463fbaaa21f677e9b21d9` | `73dec3d0536ecf1c327be9b140b06a68fc99e4a316c463fbaaa21f677e9b21d9` | **BẢO TOÀN** |
| **`admin_config.json` SHA256** | `b82806e43c5b39e95651b7057574f9d91711790a117de6364a63e0e1aea88ee8` | `b82806e43c5b39e95651b7057574f9d91711790a117de6364a63e0e1aea88ee8` | **BẢO TOÀN** |
| **Backend Unit Tests** | 34/34 passed (100%) | 34/34 passed (100%) | **BẢO TOÀN** |

---

## 5. DANH MỤC TỆP TIN ĐÃ TẠO MỚI

1. `D:\Tín\ABC\start_all.cmd`: Entry point chính của hệ thống launcher.
2. `D:\Tín\ABC\unified_launcher.py`: Script Python điều phối trung tâm.
3. `D:\Tín\ABC\test\scratch\verify_launcher_logic.py`: Script tự động hóa 9 bài kiểm thử hồi quy và an toàn tiến trình.
4. `D:\Tín\ABC\DashBoardD\docs\PHASE_7_1_UNIFIED_LAUNCHER_REPORT.md`: Báo cáo nghiệm thu kỹ thuật chi tiết.
5. `D:\Tín\ABC\test\docs\PHASE_7_1_UNIFIED_LAUNCHER_REPORT.md`: Bản sao đồng bộ tài liệu sang thư mục test.

---

## 6. ĐÁNH GIÁ TIÊU CHÍ NGHIỆM THU (ACCEPTANCE GATES)

- [x] **Tiêu chí 1 (Khởi động tiện lợi 1-Click):** Đã tạo `start_all.cmd` và menu tương tác 4 tùy chọn rõ ràng, tự kiểm tra trạng thái sức khỏe trước khi mở trình duyệt.
- [x] **Tiêu chí 2 (Tái sử dụng an toàn):** Tự động phát hiện dịch vụ đang chạy, không báo lỗi xung đột giả, không tạo tiến trình đè.
- [x] **Tiêu chí 3 (Dừng có kiểm soát):** Chỉ giải phóng các tiến trình do phiên launcher tạo ra; tuyệt đối không can thiệp tiến trình độc lập của người dùng.
- [x] **Tiêu chí 4 (Xử lý xung đột cổng thông minh):** Phát hiện tiến trình lạ và cảnh báo dừng lại thay vì cưỡng chế tắt ứng dụng.
- [x] **Tiêu chí 5 (Bảo toàn nguyên vẹn):** Cấu hình, cơ sở dữ liệu, mã nguồn nghiệp vụ camera, ticket, zalo và các script khởi chạy cũ không bị sửa đổi.

---

## 7. KẾT LUẬN & ĐIỂM DỪNG AN TOÀN

Giai đoạn **Phase 7.1 — Implement Unified Launcher** đã hoàn thành xuất sắc và đáp ứng 100% tiêu chí an toàn và nghiệp vụ đã được phê duyệt.

Hệ thống dừng tại đây và bảo toàn nguyên trạng, **chưa chuyển sang Phase 7.2**, sẵn sàng chờ chỉ thị tiếp theo từ Quản trị viên.
