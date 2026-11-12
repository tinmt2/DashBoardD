# BÁO CÁO NGHIỆM THU TÀI LIỆU VẬN HÀNH & BÀN GIAO (PHASE 7.3)
**Hệ thống:** DashBoardD & Test Application Engine  
**Thời gian thực hiện:** 11/11/2026  
**Trạng thái nghiệm thu:** **PASS (100% - HOÀN TẤT TÀI LIỆU & BÀN GIAO KỸ THUẬT)**

---

## 1. TỔNG QUAN KẾT QUẢ GIAI ĐOẠN PHASE 7.3

Giai đoạn **Phase 7.3 — Operator Documentation & Final Handover** đã hoàn tất việc xây dựng toàn bộ hệ thống tài liệu vận hành và bàn giao kỹ thuật cho hệ sinh thái tích hợp DashBoardD và Module Test Engine sau khi hoàn thành các Phase 7.1 (Triển khai Launcher) và Phase 7.2 (Kiểm toán Sẵn sàng Vận hành).

Không có tính năng mới nào được phát triển trong giai đoạn này, tuân thủ nguyên tắc thuần túy tài liệu hóa và kiểm tra tính nhất quán mã nguồn.

---

## 2. DANH MỤC TÀI LIỆU ĐÃ XÂY DỰNG & ĐỒNG BỘ

Toàn bộ tài liệu kỹ thuật được lưu trữ tại `DashBoardD/docs/` và được đồng bộ song song sang `test/docs/` để thuận tiện tra cứu cho cả hai đội ngũ:

| STT | Tài liệu | Đường dẫn tệp tin | Mục đích & Nội dung cốt lõi |
| :---: | :--- | :--- | :--- |
| **1** | **Sổ tay Vận hành Hệ thống** | [`DashBoardD/docs/OPERATIONS_RUNBOOK.md`](file:///D:/T%C3%ADn/ABC/DashBoardD/docs/OPERATIONS_RUNBOOK.md)<br>[`test/docs/OPERATIONS_RUNBOOK.md`](file:///D:/T%C3%ADn/ABC/test/docs/OPERATIONS_RUNBOOK.md) | **12 mục bắt buộc:** Kiến trúc tổng quan, điều kiện môi trường, hướng dẫn chạy qua `start_all.cmd` (Dev, Prod, Status, Exit), bảng cổng & health endpoint, hướng dẫn xử lý `CONFLICT_UNKNOWN` và Timeout, cách chạy script cũ độc lập, nguyên tắc shutdown an toàn, danh mục nghiệp vụ có tác dụng phụ, bảo vệ DB/config và quy trình Rollback. |
| **2** | **Tài liệu Bàn giao Kỹ thuật** | [`DashBoardD/docs/TECHNICAL_HANDOVER.md`](file:///D:/T%C3%ADn/ABC/DashBoardD/docs/TECHNICAL_HANDOVER.md)<br>[`test/docs/TECHNICAL_HANDOVER.md`](file:///D:/T%C3%ADn/ABC/test/docs/TECHNICAL_HANDOVER.md) | Cấu trúc phân cấp dự án, danh mục các entry point thực tế, sơ đồ phụ thuộc dịch vụ (FastAPI 8000, Test 18020, Vite 5174), đường dẫn log & config, các lệnh kiểm tra an toàn không tác dụng phụ, và các giới hạn kỹ thuật đã nhận diện. |
| **3** | **Báo cáo Nghiệm thu Phase 7.3**| [`DashBoardD/docs/PHASE_7_3_HANDOVER_REPORT.md`](file:///D:/T%C3%ADn/ABC/DashBoardD/docs/PHASE_7_3_HANDOVER_REPORT.md)<br>[`test/docs/PHASE_7_3_HANDOVER_REPORT.md`](file:///D:/T%C3%ADn/ABC/test/docs/PHASE_7_3_HANDOVER_REPORT.md) | Báo cáo chính thức tổng kết kết quả đối chiếu mã nguồn, phân định vùng kiểm chứng, xác nhận tính toàn vẹn và điểm dừng an toàn của hệ thống. |

---

## 3. KẾT QUẢ ĐỐI CHIẾU MÃ NGUỒN THỰC TẾ (SOURCE ALIGNMENT)

Toàn bộ các thông số, lệnh và cơ chế được mô tả trong tài liệu đã được đối soát 1:1 với mã nguồn đang hiện diện trên ổ đĩa:

1. **Khớp lệnh & Entry point:**
   - `start_all.cmd` -> Gọi `py -3.12 unified_launcher.py %*` (đã đối chiếu chính xác).
   - DashBoardD Backend -> `app.main:app` trên port `8000` (đã đối chiếu với `backend/app/main.py`).
   - Test Engine Backend -> `app.api.main:app` trên port `18020` (đã đối chiếu với `test/app/api/main.py`).
   - Phục vụ tĩnh SPA -> Mount `dashboard-app/dist` trên port `8000` (đã đối chiếu `backend/app/main.py` lines 57-106).
2. **Khớp Health Endpoints & Snippet:**
   - DashBoardD Backend: `http://127.0.0.1:8000/api/health` -> Phản hồi chứa `"ok"`.
   - Test Engine Backend: `http://127.0.0.1:18020/health` -> Phản hồi chứa `"test-python-backend"`.
   - Frontend Dev: `http://localhost:5174` -> Phản hồi chứa thẻ `<html`.
   - Production Server: `http://localhost:8000/` -> Phản hồi chứa thẻ `<html`.
3. **Khớp cấu hình phân giải URL (Client-side):**
   - `apiConfig.ts`: Tự động nhận diện port 5174 thì trỏ về `:8000`, ngược lại dùng `window.location.origin`.
   - `testApi/config.ts`: Ưu tiên biến môi trường, mặc định trỏ về `http://127.0.0.1:18020`.
4. **Khớp các script khởi chạy cũ:**
   - `test/run.cmd`: Đúng lệnh `npm run electron:dev` trong thư mục `desktop`.
   - `start_dev.bat`: Đúng lệnh gọi `py -3.12 run_dev.py`.
   - `start_server.bat`: Đúng lệnh chạy Uvicorn port 8000 trên `0.0.0.0`.
   - `start_unified.bat`: Đúng logic kiểm tra build `dist` trước khi chạy server.

---

## 4. PHÂN ĐỊNH VÙNG ĐÃ KIỂM CHỨNG & CHƯA KIỂM CHỨNG

### 4.1. Những phần ĐÃ KIỂM CHỨNG THỰC TẾ (100% Verified)
- Khởi chạy Unified Launcher qua `start_all.cmd` (các flag `--help`, `--status`, `--dev`, `--prod`, Interactive Menu).
- Tái sử dụng thông minh các tiến trình đang chạy mà không spawn trùng lặp hoặc restart service.
- Cơ chế No-Kill: Phát hiện xung đột cổng `CONFLICT_UNKNOWN`, dừng an toàn và không kill tiến trình lạ.
- Cơ chế Timeout và dọn dẹp có kiểm soát: Chỉ kill tiến trình nằm trong `SPAWNED_PROCESSES`, bảo toàn tuyệt đối các PID pre-existing (20896, 23724, 11372).
- Bảo vệ bản build `dist`: Không bao giờ chạy build đè khi `dist/index.html` đã tồn tại.
- Toàn bộ **34/34 backend pytest unit tests** chạy đạt 100% PASS.
- Toàn bộ **9/9 operational readiness scenarios** chạy đạt 100% PASS.
- Cơ chế xác thực Admin (JWT Bearer Token, TOTP 2FA, token TTL 15 phút, Revocation Blocklist tại `/api/admin/logout`).

### 4.2. Những phần CHƯA KIỂM CHỨNG BẰNG THAO TÁC THỰC TẾ (Static Audit Only)
Để đảm bảo an toàn tuyệt đối cho thiết bị mạng và dữ liệu sản xuất của doanh nghiệp, các thao tác sau **không được kích hoạt thực tế** mà chỉ được kiểm toán cấu trúc mã nguồn:
- **Quét mạng Camera RTSP/DVR thật:** Không phát lệnh quét dải IP LAN nhằm tránh làm nghẽn lưu lượng switch/router công ty.
- **Tạo Ticket SSC thật:** Không gọi API tạo ticket nhằm tránh sinh rác dữ liệu trên hệ thống SSC hỗ trợ kỹ thuật.
- **Gửi tin nhắn Zalo thật:** Không gửi payload tin nhắn ra ngoài để tránh phát sinh chi phí ZNS và làm phiền khách hàng.
- **Auto-Sync crawl dữ liệu thật:** Không kích hoạt crawler đè dữ liệu mới và không ghi dòng vào Google Sheets sản xuất.

---

## 5. CÁC ĐIỂM CẦN LƯU Ý KHI VẬN HÀNH (OPERATIONAL RECOMMENDATIONS)

1. **Địa chỉ ràng buộc mạng của Test Engine:**
   - Test Engine bind tại `127.0.0.1:18020`. Nếu có nhu cầu cho phép máy tính khác trong mạng nội bộ LAN điều khiển module test từ xa qua địa chỉ IP máy chủ (`http://10.96.25.111:8000`), Kỹ sư vận hành cần cân nhắc chuyển bind host sang `0.0.0.0` trong `unified_launcher.py` và cấu hình CORS phù hợp.
2. **Quyền hạn tài khoản Windows:**
   - Để kiểm soát toàn diện các xung đột cổng từ các service chạy ngầm dưới quyền Administrator, khuyến nghị Quản trị viên khởi chạy `start_all.cmd` bằng cửa sổ Command Prompt với quyền quản trị (Run as Administrator) khi cần bảo trì.

---

## 6. XÁC NHẬN TÍNH TOÀN VẸN CƠ SỞ DỮ LIỆU & MÃ NGUỒN

| Đối tượng | Trạng thái ghi nhận | Đánh giá |
| :--- | :--- | :---: |
| **`DashBoardD/backend/opsmonitor.db`** | Kích thước: `27,009,024 bytes`<br>SHA256: `73dec3d0536ecf1c327be9b140b06a68fc99e4a316c463fbaaa21f677e9b21d9` | **BẢO TOÀN 100%** |
| **`DashBoardD/backend/app/admin_config.json`** | SHA256: `b82806e43c5b39e95651b7057574f9d91711790a117de6364a63e0e1aea88ee8` | **BẢO TOÀN 100%** |
| **Mã nguồn Production** | Không có bất kỳ tệp `.py`, `.ts`, `.tsx` nào bị sửa đổi trong Phase 7.3 | **BẢO TOÀN 100%** |
| **Các script khởi chạy cũ** | `test/run.cmd`, `start_dev.bat`, `start_server.bat`, `start_unified.bat`, `open_desktop_app.bat` | **BẢO TOÀN 100%** |

---

## 7. KẾT LUẬN & ĐIỂM DỪNG BÀN GIAO TOÀN DIỆN

Giai đoạn **Phase 7.3 — Operator Documentation & Final Handover** đã kết thúc thành công:
- Toàn bộ tài liệu vận hành (`OPERATIONS_RUNBOOK.md`) và tài liệu bàn giao kỹ thuật (`TECHNICAL_HANDOVER.md`) đã được biên soạn đầy đủ, chi tiết, bám sát thực tế mã nguồn và được đồng bộ song phương giữa `DashBoardD/docs` và `test/docs`.
- Hệ sinh thái tích hợp giữa DashBoardD và Module Test Engine đã đạt mức độ hoàn thiện cao nhất, an toàn, ổn định và sẵn sàng cho việc đưa vào khai thác sử dụng.

Hệ thống dừng tại đây và bảo toàn nguyên trạng, **chưa chuyển sang Phase 7.4**, hoàn tất toàn bộ chuỗi nhiệm vụ của Phase 7 và sẵn sàng chờ chỉ thị tiếp theo từ Quản trị viên.
