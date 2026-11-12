# BÁO CÁO HỒI QUY BẢO MẬT & NGHIỆM THU ĐỘC LẬP (PHASE 6C.2)

**Thời gian thực hiện:** 11/11/2026  
**Dự án:** `DashBoardD` tích hợp module `Test-LC`  
**Chuyên môn áp dụng:** Security Auditor & Quality Assurance Specialist  
**Mục tiêu:** Nghiệm thu độc lập, kiểm thử hồi quy 5 Gates và xác minh độ tin cậy sau khi khắc phục các lỗ hổng SEC-01 đến SEC-05 và lỗi route `#/departments`.  
**Quy tắc an toàn tuân thủ:** Tuyệt đối không sửa code production trong Phase 6C.2; bảo toàn nguyên vẹn database `opsmonitor.db` và cấu hình `admin_config.json`; không gọi tác vụ mutation có tác động thật.

---

## 1. KẾT QUẢ TỔNG QUAN 5 GATES

| Cổng kiểm thử | Đối tượng kiểm tra | Số ca kiểm thử | Kết quả | Đánh giá |
| :--- | :--- | :---: | :---: | :--- |
| **Gate A — Xác thực Backend** | 9 endpoint nhạy cảm (Inside, Auto-Sync, Admin) | 27 ca | **PASS** | Chặn 401 triệt để tại backend khi thiếu token hoặc token sai; 200 cho safe read |
| **Gate B — Token TTL & Vòng đời phiên** | Định dạng token, TTL 8h, Auto-prune, Logout, Reboot | 6 ca | **PASS** | Token hết hạn bị loại bỏ; logout thu hồi token ngay; dữ liệu phiên bền vững |
| **Gate C — Hồi quy Frontend & API Client** | `Admin.tsx`, `insideApi.ts`, `autoSyncApi.ts`, Test Center | 5 luồng | **PASS** | UI bảo vệ an toàn, đính kèm token chuẩn, xử lý 401 không làm sập ứng dụng |
| **Gate D — Router & Điều hướng** | 18 tuyến đường (Core, Admin, Test routes, Fallback) | 18 ca | **PASS** | 100% route render mượt mà, chuyển hướng đúng đích, không màn hình trắng hay loop |
| **Gate E — Bảo toàn & Chất lượng Code** | Checksum Database, Config, Build, Lint, Pytest | 5 mục | **PASS / CONDITIONAL** | Database SHA256 nguyên vẹn 100%, Build 0 lỗi, Lint 0 lỗi, 29/32 pytest pass |

---

## 2. MA TRẬN TEST XÁC THỰC BACKEND (GATE A)

Tất cả các endpoint nhạy cảm đã được kiểm thử với 3 trạng thái:
1. **Không có token (No Token)**: Kỳ vọng `HTTP 401 Unauthorized`.
2. **Token giả mạo / Không hợp lệ (Invalid Token)**: Kỳ vọng `HTTP 401 Unauthorized`.
3. **Token Admin hợp lệ**: Áp dụng cho các endpoint đọc dữ liệu an toàn (`Safe Read`). Các endpoint mutation được bảo vệ an toàn bằng cách kiểm tra chặn ở tầng xác thực và đối soát mã nguồn (`Source Audit`) để bảo toàn dữ liệu sản xuất.

| Endpoint | Method | Phân nhóm | Không có Token | Token không hợp lệ | Token Admin hợp lệ | Loại bằng chứng | Trạng thái |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :---: |
| `/api/inside/creds` | GET | Inside | `HTTP 401` | `HTTP 401` | `HTTP 200` | API Test | **PASS** |
| `/api/inside/creds` | POST | Inside | `HTTP 401` | `HTTP 401` | `SKIPPED (Mutation)` | API Test / Source Audit | **PASS** |
| `/api/auto-sync/config` | POST | Auto-Sync | `HTTP 401` | `HTTP 401` | `SKIPPED (Mutation)` | API Test / Source Audit | **PASS** |
| `/api/auto-sync/run-now` | POST | Auto-Sync | `HTTP 401` | `HTTP 401` | `SKIPPED (Mutation)` | API Test / Source Audit | **PASS** |
| `/api/admin/logs` | GET | Admin | `HTTP 401` | `HTTP 401` | `HTTP 200` | API Test | **PASS** |
| `/api/admin/logs` | DELETE | Admin | `HTTP 401` | `HTTP 401` | `SKIPPED (Mutation)` | API Test / Source Audit | **PASS** |
| `/api/admin/overview` | GET | Admin | `HTTP 401` | `HTTP 401` | `HTTP 200` | API Test | **PASS** |
| `/api/admin/test-sync/fpt` | POST | Admin | `HTTP 401` | `HTTP 401` | `SKIPPED (Mutation)` | API Test / Source Audit | **PASS** |
| `/api/admin/logout` | POST | Admin | `HTTP 200` | `HTTP 200` | `HTTP 200` (Thu hồi thành công) | API Test | **PASS (Idempotent)** |

> **Kiểm kê 61 OpenAPI Routes:** Đã quét tự động toàn bộ 61 endpoint của `app.main:app`. Các endpoint phục vụ hiển thị Dashboard mở (`/api/employees`, `/api/fpt-shop/data`, `/api/long-chau/summary`, `/api/health`, `/api/notifications`) không chứa bí mật hệ thống. Toàn bộ 100% các endpoint quản trị hạ tầng, tài khoản bảo mật và trigger ngầm đều đã được bảo vệ bằng `verify_admin_token`.

---

## 3. KẾT QUẢ KIỂM THỬ TOKEN TTL VÀ VÒNG ĐỜI PHIÊN (GATE B)

Đã chạy bộ kịch bản kiểm thử độc lập `test/scratch/test_gate_a_and_b.py` và `test/scratch/test_logout_http.py` sử dụng kỹ thuật Clock Injection mà không thay đổi TTL cấu hình sản xuất:

| Mục kiểm tra | Kịch bản thực hiện | Kết quả kỳ vọng | Kết quả thực tế | Loại bằng chứng | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **B1. Format Validation** | Header rỗng / Sai schema / Token rỗng | `HTTP 401` | Bị từ chối với thông báo lỗi tương ứng | Unit Test | **PASS** |
| **B2. TTL Fresh Token** | Token hợp lệ tuổi = 1h (< 8h TTL) | `HTTP 200` | Xác thực thành công | Unit Test / Clock Injection | **PASS** |
| **B3. TTL Expired Token** | Token tuổi = 9h (> 8h TTL) | `HTTP 401` | Bị từ chối với lỗi phiên hết hạn | Unit Test / Clock Injection | **PASS** |
| **B4. Auto-pruning** | Kiểm tra danh sách token sau khi token hết hạn truy cập | Token hết hạn bị xóa khỏi JSON | Token quá hạn bị loại bỏ ngay lập tức | Unit Test / Source Audit | **PASS** |
| **B5. Logout Revocation** | Gọi `POST /api/admin/logout` rồi dùng lại token | `HTTP 401` ở lần gọi sau | Token bị thu hồi trên backend; lần gọi sau bị từ chối 401 | API Test | **PASS** |
| **B6. Reboot Persistence** | Khởi động lại backend server | Token hợp lệ vẫn dùng được | Token lưu trong `admin_config.json` kèm `created_at`, duy trì phiên đúng TTL | Source Audit / API Test | **PASS** |

---

## 4. KẾT QUẢ HỒI QUY FRONTEND & API CLIENT (GATE C)

| Component / Luồng | Hành vi xác thực | Xử lý lỗi & 401 | Loại bằng chứng | Trạng thái |
| :--- | :--- | :--- | :--- | :---: |
| **`Admin.tsx` (Quản trị)** | Form đăng nhập hiển thị khi chưa có token; chỉ gọi API nhạy cảm khi có token | Khi nhận 401 hoặc token hết hạn, tự xóa `localStorage` và chuyển về login form | Browser E2E / Source Audit | **PASS** |
| **`insideApi.ts` (Inside)** | Tự động lấy Bearer token từ `localStorage` đính kèm vào header | Bắt lỗi 401 an toàn không làm sập layout dashboard | Source Audit | **PASS** |
| **`autoSyncApi.ts` (Auto-Sync)** | Đính kèm `Authorization: Bearer <token>` cho config update và run-now | Trả về thông báo lỗi rõ ràng qua feedback UI | Source Audit | **PASS** |
| **Test Control Center (`#/admin`)** | Giao diện điều khiển tách biệt, kết nối Test Backend `127.0.0.1:18020` | Hiển thị trạng thái Online và số lượng 3,725 shop chính xác | Browser E2E | **PASS** |
| **Layout Header Profile** | Nút mở modal thông tin Inside Account | Khi chưa đăng nhập Admin, không thể đọc thông tin credential | Browser E2E | **PASS** |

---

## 5. KẾT QUẢ KIỂM THỬ ROUTER & ĐIỀU HƯỚNG (GATE D)

Subagent `Full Route Regression Verifier` (Conversation ID `bc1b3a90-90d8-4cb6-b59c-1173bf52619e`) đã điều khiển trình duyệt kiểm chứng độc lập toàn bộ 18 tuyến đường:

| # | URL Kiểm tra | URL Quan sát thực tế | Giao diện hiển thị | Blank / Crash | Loại bằng chứng | Trạng thái |
| :-: | :--- | :--- | :--- | :-: | :--- | :---: |
| 1 | `http://localhost:5174/#/` | `#/dashboard` | Dashboard Tổng quan (3 chuỗi) | Không | Browser E2E | **PASS** |
| 2 | `http://localhost:5174/#/analytics` | `#/analytics` | Phân tích lỗi chi tiết | Không | Browser E2E | **PASS** |
| 3 | `http://localhost:5174/#/departments` | `#/employees` | **Quản lý nhân viên (Redirect chuẩn)** | Không | Browser E2E | **PASS** |
| 4 | `http://localhost:5174/#/employees` | `#/employees` | Quản lý nhân viên (37 nhân sự 3 chuỗi) | Không | Browser E2E | **PASS** |
| 5 | `http://localhost:5174/#/admin` | `#/admin` | Test Operations Control Center | Không | Browser E2E | **PASS** |
| 6 | `http://localhost:5174/#/admin/system` | `#/admin/system` | Quản trị hệ thống (Form đăng nhập) | Không | Browser E2E | **PASS** |
| 7 | `http://localhost:5174/#/admin/camera` | `#/admin/camera` | Check Camera & DVR Device Monitoring | Không | Browser E2E | **PASS** |
| 8 | `http://localhost:5174/#/admin/ticket` | `#/admin/ticket` | Ticket SSC Automation Manager | Không | Browser E2E | **PASS** |
| 9 | `http://localhost:5174/#/admin/motion` | `#/admin/motion` | Motion Analytics Excel/CSV Viewer | Không | Browser E2E | **PASS** |
| 10 | `http://localhost:5174/#/admin/zalo` | `#/admin/zalo` | Zalo Security Monitor Console | Không | Browser E2E | **PASS** |
| 11 | `http://localhost:5174/#/admin/settings` | `#/admin/settings` | Cài đặt hệ thống Test & Sync Config | Không | Browser E2E | **PASS** |
| 12 | `http://localhost:5174/#/test` | `#/admin` | Redirect về Test Control Center | Không | Browser E2E | **PASS** |
| 13 | `http://localhost:5174/#/test/camera` | `#/admin/camera` | Redirect về Check Camera | Không | Browser E2E | **PASS** |
| 14 | `http://localhost:5174/#/test/ticket` | `#/admin/ticket` | Redirect về Ticket SSC | Không | Browser E2E | **PASS** |
| 15 | `http://localhost:5174/#/test/motion` | `#/admin/motion` | Redirect về Motion Analytics | Không | Browser E2E | **PASS** |
| 16 | `http://localhost:5174/#/test/zalo` | `#/admin/zalo` | Redirect về Zalo Monitor | Không | Browser E2E | **PASS** |
| 17 | `http://localhost:5174/#/test/settings` | `#/admin/settings` | Redirect về Cài đặt Test | Không | Browser E2E | **PASS** |
| 18 | `http://localhost:5174/#/random-unknown-404-page` | `#/dashboard` | **Fallback toàn cục về Dashboard** | Không | Browser E2E | **PASS** |

> **Bằng chứng ảnh chụp thực tế:**
> - Tuyến `#/departments` -> `#/employees`: Bằng chứng Browser screenshot tại step 6.
> - Tuyến fallback URL ngẫu nhiên -> `#/dashboard`: Bằng chứng `browser_evidence/bc1b3a90-90d8-4cb6-b59c-1173bf52619e/final_step_14.png`.

---

## 6. KẾT QUẢ BUILD, LINT VÀ CHẤT LƯỢNG MÃ NGUỒN (GATE E)

| Hạng mục kiểm tra | Công cụ thực hiện | Kết quả thực tế | Loại bằng chứng | Trạng thái |
| :--- | :--- | :--- | :--- | :---: |
| **Frontend Production Build** | `tsc -b && vite build` | Hoàn tất trong **520ms**, tạo dist sạch | Source Build | **PASS** |
| **Frontend Code Linting** | `oxlint` (60 files) | **0 errors** (139 non-blocking warnings) | Static Analysis | **PASS** |
| **Backend Unit Tests** | `pytest tests/ -v` (32 tests) | **29 PASSED**, 3 FAILED (Xem Mục 7) | Unit Test | **CONDITIONAL** |
| **Database Integrity Check** | SHA256 Checksum | `73dec3d0536ecf1c327be9b140b06a68fc99e4a316c463fbaaa21f677e9b21d9` | Checksum Hash | **PASS** |
| **Admin Config Integrity Check** | Cấu trúc JSON & Key Check | Password hash và TOTP secret nguyên vẹn | File Integrity | **PASS** |

---

## 7. CÁC LỖI / PHÁT HIỆN CÒN TỒN TẠI VÀ PHƯƠNG ÁN KHẮC PHỤC

Tuân thủ quy tắc không tự ý sửa mã trong Phase 6C.2, các phát hiện được ghi nhận chi tiết:

### Phát hiện 1: Lỗi Unit Test do gọi hàm trực tiếp không qua FastAPI Dependency Injection
- **Tệp tin:** [`DashBoardD/backend/app/core/auth.py`](file:///D:/T%C3%ADn/ABC/DashBoardD/backend/app/core/auth.py) dòng 34 & [`backend/tests/unit/test_auto_sync_api.py`](file:///D:/T%C3%ADn/ABC/DashBoardD/backend/tests/unit/test_auto_sync_api.py)
- **Nguyên nhân:** Khi gọi hàm Python trực tiếp trong test mà không truyền `authorization`, giá trị mặc định là đối tượng `fastapi.params.Header` (thay vì chuỗi). Lệnh `authorization.startswith("Bearer ")` ném ra `AttributeError`.
- **Mức độ rủi ro:** Thấp (Low). Ứng dụng thực tế chạy qua HTTP không bị ảnh hưởng.
- **Phương án đề xuất sửa (Chờ phê duyệt):**
  Trong `auth.py`, sửa điều kiện:
  ```python
  if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
      raise HTTPException(status_code=401, detail="Chưa có token xác thực!")
  ```

### Phát hiện 2: Bộ Unit Test cũ kỳ vọng API Inside không cần xác thực
- **Tệp tin:** [`DashBoardD/backend/tests/unit/test_inside_api.py`](file:///D:/T%C3%ADn/ABC/DashBoardD/backend/tests/unit/test_inside_api.py) dòng 9 và 17.
- **Nguyên nhân:** Test case cũ kỳ vọng gọi GET/POST `/api/inside/creds` không có token trả về `200 OK` (chính là lỗ hổng SEC-01 cũ). Do backend hiện đã chặn 401 đúng chuẩn, test cũ này báo `assert 401 == 200`.
- **Mức độ rủi ro:** Không có rủi ro (đây là bằng chứng xác nhận bản vá bảo mật đã có hiệu lực).
- **Phương án đề xuất sửa (Chờ phê duyệt):** Cập nhật test case bổ sung header `Authorization: Bearer <token>` khi kỳ vọng 200 và bổ sung test case xác minh 401 khi thiếu token.

### Phát hiện 3: Endpoint `POST /api/admin/logout` có tính chất Idempotent
- **Tệp tin:** [`DashBoardD/backend/app/api/admin.py`](file:///D:/T%C3%ADn/ABC/DashBoardD/backend/app/api/admin.py).
- **Hiện trạng:** Trả về `{"success": true}` ngay cả khi không có token (idempotent logout). Nếu có token, thực hiện thu hồi token.
- **Phương án đề xuất:** Giữ nguyên theo chuẩn REST idempotent hoặc thêm `verify_admin_token(authorization)` nếu Quản trị viên yêu cầu bắt buộc phải có token hợp lệ mới được đăng xuất.

---

## 8. CÁC CA KIỂM THỬ CHƯA CHẠY TRỰC TIẾP & LÝ DO

Để bảo toàn tuyệt đối cơ sở dữ liệu và tránh side-effects:
1. `POST /api/inside/creds` với dữ liệu ghi thật: Đã kiểm tra chặn 401 khi không có token; không ghi dữ liệu thật để tránh ảnh hưởng tài khoản.
2. `POST /api/auto-sync/config` & `POST /api/auto-sync/run-now`: Đã kiểm tra chặn 401; không kích hoạt tiến trình cào dữ liệu ngầm.
3. `DELETE /api/admin/logs`: Đã kiểm tra chặn 401; không xóa nhật ký đang ghi của hệ thống.
4. `POST /api/admin/test-sync/fpt`: Đã kiểm tra chặn 401; không khởi động Selenium Chrome cào dữ liệu thật.

*Tất cả các endpoint trên đều được xác minh 2 lớp: kiểm thử chặn HTTP 401 trên môi trường thật và kiểm toán mã nguồn xác nhận hàm `verify_admin_token(authorization)` nằm ở dòng đầu tiên của hàm.*

---

## 9. DANH SÁCH TỆP THAY ĐỔI TRONG PHASE 6C.2

- **Tệp code production bị sửa:** **0 tệp** (Tuân thủ nghiêm ngặt quy tắc không sửa code).
- **Tệp phục vụ kiểm thử (Scratch):**
  - `test/scratch/check_integrity.py`
  - `test/scratch/inspect_all_routes.py`
  - `test/scratch/test_gate_a_and_b.py`
  - `test/scratch/test_logout_http.py`

---

## 10. BẰNG CHỨNG TOÀN VẸN CẤU HÌNH & DATABASE

```
[BẰNG CHỨNG ĐỐI SOÁT TOÀN VẸN MẬT MÃ]
- Database Path:   D:\Tín\ABC\DashBoardD\backend\opsmonitor.db
- Dung lượng:      27,009,024 bytes (Chính xác từng byte)
- Checksum SHA256: 73dec3d0536ecf1c327be9b140b06a68fc99e4a316c463fbaaa21f677e9b21d9 (Khớp tuyệt đối 100%)
- Admin Config:    D:\Tín\ABC\DashBoardD\backend\app\admin_config.json
  + admin_username:      admin (Nguyên vẹn)
  + admin_password_hash: Nguyên vẹn
  + totp_secret:         Nguyên vẹn
  + active_tokens:       1 token hợp lệ còn trong hạn TTL
```

---

## 11. ĐIỀU KIỆN KẾT THÚC & ĐỀ XUẤT BƯỚC TIẾP THEO

Phase 6C.2 đã hoàn thành trọn vẹn và dừng tại đây. Không có launcher 1-click nào được tạo, không dọn dẹp file ngoài ý muốn và chưa chuyển sang Phase 7.

**Đề xuất hành động tiếp theo:**
- **Lựa chọn 1 (Khuyến nghị):** Duyệt cho phép chỉnh sửa nhỏ 1 dòng trong `auth.py` (`isinstance(authorization, str)`) và cập nhật 2 tệp test case cũ (`test_auto_sync_api.py`, `test_inside_api.py`) để đưa `pytest` đạt 32/32 (100% PASS), sau đó chính thức mở **Phase 7**.
- **Lựa chọn 2:** Giữ nguyên hiện trạng, chính thức đóng Phase 6C và tiến hành lập kế hoạch cho **Phase 7**.

Kính chờ quyết định từ Quản trị viên!
