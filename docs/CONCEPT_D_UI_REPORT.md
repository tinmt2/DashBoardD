# Concept D — Pastel Calllog Operations UI Report

## 1. Design Decisions
- **Mục tiêu cốt lõi**: Tạo ra một giao diện "Light Premium SaaS" chuyên biệt cho việc giám sát lỗi Calllog/Ticket, loại bỏ hoàn toàn các yếu tố về giám sát camera hay thiết bị phần cứng.
- **Visual Hierarchy**: Thiết lập phân cấp thị giác rõ ràng: `Label (nhỏ, uppercase) -> Number (to, bold) -> Supporting Text (nhỏ, màu nhạt)`.
- **Màu sắc Pastel**: Lấy cảm hứng từ không gian làm việc nhẹ nhàng, sử dụng các dải màu pastel (Blue, Mint, Coral) để đánh dấu các trạng thái lỗi nhằm giảm bớt sự căng thẳng (cognitive load) khi giám sát trong thời gian dài.
- **Loại bỏ Visual Noise**: Không dùng donut chart phức tạp, không dùng sparklines. Thay vào đó, tập trung vào **Horizontal Progress Bars** giúp người dùng dễ dàng so sánh trực quan (quét dọc) các lỗi và chuỗi.

## 2. Color Tokens (Hệ thống màu)
- **Background**: `#F3F7FA` (Xanh xám cực nhạt, dịu mắt)
- **Surface (Card)**: `#FFFFFF`
- **Primary Navy**: `#263B59` (Dành cho text nhấn, active state)
- **Text Primary**: `#26344A` (Cho các con số và tiêu đề)
- **Text Secondary / Muted**: `#718096`
- **Border**: `#E4EBF2`
- **Pastel Colors (Chains & Errors)**:
  - FPT Shop (Coral): `#FFB3B3`
  - Long Châu (Blue): `#6FA8FF` / `#A9D8F5`
  - Vaccine (Mint): `#A8E6CF`
- **Cảnh báo (Warning/Error)**:
  - Lỗi cao / Cần chú ý (Error): `#F27777`
  - Cảnh báo nhân sự (Warning): `#FFD580`

## 3. Component Changes
- **Page Header**: Xây dựng lại layout Header riêng biệt cho Concept D, thêm bộ lọc thời gian `24 giờ | 7 ngày | 30 ngày` bằng pill-shaped segmented control với hiệu ứng active là màu pastel blue/navy nhạt.
- **KPI Cards**: Sử dụng bo góc 20px, loại bỏ hiệu ứng kính mờ (glassmorphism) quá đà, thay bằng nền trắng đặc và shadow cực nhẹ `shadow-sm`. Số lượng to, icon được đặt gọn trong vòng tròn pastel nhỏ xíu ở góc trái.
- **Top Loại Lỗi & Lỗi Theo Chuỗi**: Thay vì dùng Recharts (Donut) nặng nề, đã thiết kế custom **Horizontal Progress Bars** bằng Tailwind. Render nhanh, không lỗi layout, cực kỳ dễ đọc.

## 4. UX Rationale (Lý do chọn UX)
- **Thời gian nhận biết < 3s**: Các con số lớn (44px) giúp nhận biết ngay tổng lỗi. Progress bars giúp mắt chỉ cần quét một đường dọc là thấy ngay chuỗi nào hay loại lỗi nào chiếm đa số.
- **Micro-interactions**: Hover vào card sẽ nổi bóng nhẹ (`hover:shadow-md`), hover vào progress bar hay item danh sách nhân viên sẽ đổi nền sang `#F3F7FA`, giúp tập trung mắt vào item đang xem mà không làm loạn thị giác (không bounce, không scale to).

## 5. Những Gì Chưa Thay Đổi
- **Backend / Business Logic**: Hoàn toàn giữ nguyên, chưa can thiệp vào bất kỳ API nào.
- **Data Model**: Tiếp tục sử dụng `mockData` hiện có (calllog errors, employee ranking...).
- **Main Dashboard (`Dashboard.tsx`)**: Vẫn giữ nguyên thiết kế cũ, chỉ trình bày Concept D trên route `/ui-concepts` để chờ phê duyệt.
