# CONCEPT D — FINAL PASTEL CALLLOG UI REPORT

## Design Tokens
- **Background**: `#F3F7FA` (Màu xanh xám nhạt, tạo không khí thoáng đãng)
- **Cards**: Nền `#FFFFFF` (trắng tinh), bo góc 24px (cho block lớn) và 20px (cho KPI nhỏ), viền cực nhạt `#E4EBF2`.
- **Primary Text**: `#26344A` (Navy sẫm)
- **Secondary Text**: `#718096`
- **Pastel Palette (Accent)**: 
  - FPT Shop (Coral): `#FFB3B3`
  - Long Châu (Blue): `#6FA8FF` / `#A9D8F5`
  - Vaccine (Mint): `#A8E6CF`
  - Warning/Medium Severity: `#FFD580`
  - Error/High Severity: `#F27777`

## Component Architecture (Modular)
Toàn bộ Concept D đã được bóc tách ra các component độc lập tái sử dụng được, lưu trong thư mục `src/components/dashboard/concept/`:
1. `DashboardHeader.tsx`: Chứa Title, Subtitle, Segmented Control chọn thời gian (24h/7d/30d), và các nút cài đặt/refresh.
2. `DashboardFilters.tsx`: Hàng filter ngang chuẩn SaaS (chuỗi, nhân viên).
3. `KPIGrid.tsx` & `KPICard.tsx`: Lưới KPI hiển thị 4 metrics chính, thiết kế layout phân cấp: label nhỏ, số lớn `tabular-nums` (38px), không icon thừa, focus vào data.
4. `ErrorByChain.tsx`: Card danh sách lỗi theo chuỗi, thay vì donut chart thì dùng Horizontal Progress Bar hiển thị % và lỗi.
5. `EmployeeErrorList.tsx`: Xếp hạng 4 nhân viên có lỗi nhiều nhất, sử dụng list nhẹ nhàng với avatar.
6. `ErrorTypeList.tsx`: Danh sách top các loại lỗi phổ biến (Thiếu thông tin, sai phân loại...) có progress bar đánh dấu severity color code.

## UX Decisions & Rationale
- **Prioritize CLARITY > DECORATION**: Đã loại bỏ hoàn toàn Line Chart, Donut Chart vì chúng làm phân tán sự chú ý. Progress bars ngang là format tối ưu nhất để mắt người lướt qua nhanh (scanning).
- **Đáp ứng mục tiêu 3-5s**:
  - Nhìn lên góc trên trái: Biết ngay tổng lỗi là 872.
  - Lướt giữa: FPT Shop đang có lỗi nhiều nhất (màu đỏ pastel coral).
  - Lướt dưới: Lỗi "Thiếu thông tin" chiếm trọng số lớn nhất.
- **Accessibility & Fonts**: Dùng CSS `fontVariantNumeric: 'tabular-nums'` ở các chỗ cần hiện số liệu (KPI, Errors count) để đảm bảo các con số gióng hàng thẳng nhau hoàn hảo, tăng cường readability.

## Before/After Changes
- **Before**: UI là nguyên khối liền mạch bên trong `Dashboard.tsx`, quá tải về mặt components, dùng pie chart bị che khuất, quá nhiều màu sặc sỡ và hiệu ứng kính mờ không phù hợp với context Operation SaaS.
- **After**: UI dạng modular, 100% Light Mode, background nhẹ nhàng, chia layout chuẩn Desktop, tập trung 100% vào việc "tìm lỗi" (Error Monitoring).

## Validation Results
- [x] TypeScript compiler pass 100% (`tsc -b`).
- [x] Các component đã được tách riêng hoàn chỉnh.
- [x] Không làm hỏng Dashboard cũ, Concept D chạy độc lập trong `/ui-concepts`.
- [x] Layout tương thích tuyệt vời trên độ phân giải `1440x900` và `1920x1080`.
- [x] Hoàn toàn KHÔNG có metrics liên quan đến Camera/Thiết bị.
