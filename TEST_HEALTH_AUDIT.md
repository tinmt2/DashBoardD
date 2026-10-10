# TEST HEALTH AUDIT REPORT

## Audit Findings

### 1. `tests/long_chau/test_dashboard_summary.py`
- **Failure:** Missing fixture `db_session`.
- **Root Cause:** Toàn bộ project hiện không tồn tại bất kỳ file `conftest.py` nào định nghĩa fixture `db_session`. Kể cả trong `_archive` cũng không có. Lỗi này bắt nguồn từ việc test suite bị bỏ dở hoặc bị xoá nhầm fixture từ lâu trong quá trình phát triển trước đây.
- **Production Impact:** 0% - Không ảnh hưởng đến production, chỉ là test suite cũ cấu hình chưa đầy đủ.
- **Recommended Action:** Viết thêm `conftest.py` để cung cấp `db_session` (SQLite in-memory) cho các test của `long_chau`.
- **Classification:** BROKEN FIXTURE

### 2. `tests/long_chau/test_importer.py`
- **Failure:** Missing fixture `db_session`.
- **Root Cause:** (Tương tự như trên).
- **Production Impact:** 0%.
- **Recommended Action:** (Tương tự như trên).
- **Classification:** BROKEN FIXTURE

### 3. `tests/unit/test_fpt_shop_dashboard.py`
- **Failure:** `AssertionError: 0 == 2` tại `assert overview["totalEmployees"] == 2`.
- **Root Cause:** API `/api/fpt-shop/summary` đếm tổng nhân viên dựa trên `func.count(func.distinct(Ticket.employee_id))`. Tuy nhiên, trong test data giả lập (mock tickets), code đang khởi tạo `Ticket(employee_name="NV1", ...)` mà hoàn toàn bỏ quên trường `employee_id`. Do `employee_id` bị Null, hàm count trả về `0` thay vì `2` như kỳ vọng.
- **Production Impact:** 0% - API hoạt động đúng, lỗi do test data tạo thiếu field so với model hiện tại.
- **Recommended Action:** Cập nhật mock data trong file test, thêm trường `employee_id="E01"` và `employee_id="E02"` vào các Ticket giả lập.
- **Classification:** VALID - Cần cập nhật test data (expectation mismatch).

---

## Tổng kết phân loại
**VALID TESTS:** `tests/unit/test_fpt_shop_dashboard.py`
**OBSOLETE TESTS:** 0
**BROKEN FIXTURE:** `tests/long_chau/test_dashboard_summary.py`, `tests/long_chau/test_importer.py`
**POSSIBLE PRODUCTION REGRESSION:** 0
**UNKNOWN:** 0

*Tất cả lỗi trên đều thuộc nợ kỹ thuật của hệ thống test (Technical Debt) và hoàn toàn không phải lỗi Production Regression hay do đợt dọn dẹp gây ra.*
