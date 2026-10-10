# DASHBOARD DESIGN EXPLORATION

Giai đoạn thăm dò thiết kế giao diện Dashboard theo định hướng **Calllog / Ticket Quality Monitoring** thay cho phong cách NOC / Server Monitoring cũ.

Tất cả 5 concept đều dùng chung nguồn dữ liệu Mock thực tế, loại bỏ hoàn toàn các khái niệm về Camera, Device, Server.

## Danh sách Concepts

### Concept 01 — Soft SaaS
- **Palette:** Trắng, xanh dương nhạt (Pastel Blue: `#8CC8F5`), xanh ngọc (Mint: `#7DDCC5`).
- **Background:** `#F5F9FC`.
- **Đặc điểm:** Background rất sáng, card trắng viền nhẹ `#E2EAF0`, bo góc lớn `rounded-2xl`, shadow cực mỏng `shadow-[0_2px_10px_rgba(0,0,0,0.02)]`. Cảm giác thân thiện, nhẹ nhàng đặc trưng của các app SaaS B2B hiện đại.
- **Bố cục chính:**
  - Hàng KPI 4 thẻ lớn ngang nhau (tổng lỗi, tổng kiểm tra, tỷ lệ lỗi, nhân sự).
  - Khối "Phân bổ theo chuỗi" dùng thanh Progress Bar lớn ngang.
  - "Nhân viên cần chú ý" dùng grid card dạng lưới.

### Concept 02 — Mint Operations
- **Palette:** Teal / Cyan đậm dần.
- **Background:** `#F0F7F4`.
- **Đặc điểm:** Táo bạo hơn Concept 1 với thẻ KPI chính ("Tổng Lỗi") sử dụng Gradient to bản nổi bật `from-teal-400 to-teal-500` và typography lớn `text-6xl`. Các thẻ khác có hover state và visual assets (vòng tròn màu làm nền).
- **Bố cục chính:**
  - KPI Hero card to nhất góc trái trên, ghép với 2 KPI phụ ở dưới.
  - "Lỗi theo chuỗi" dùng Floating text (Chữ lớn nổi bật trên nền trắng, có vạch chéo/glow ở góc).
  - Bảng nhân viên hiển thị dạng danh sách thay vì lưới (Avatar + Tên bên trái, Lỗi bên phải).

### Concept 03 — Modern NOC Light
- **Palette:** Trắng, xám xanh (Blue-gray / Slate), Cam cảnh báo (Warning).
- **Background:** `#F7FAFC`.
- **Đặc điểm:** Typography gãy gọn hơn, nhiều chữ in hoa `uppercase tracking-widest font-mono`, viền nét cứng `rounded-none border-slate-200`. Có cảm giác của màn hình giám sát kỹ thuật (Operations/NOC) nhưng không bị tối mắt (chuyển sang nền sáng). Information Density cao.
- **Bố cục chính:**
  - Viền cứng không bo góc, không shadow.
  - Component "Lỗi theo chuỗi" và "Phân loại lỗi" thu nhỏ, nhường không gian.
  - Chữ số KPI chính to nhưng nét mảnh `font-bold tracking-tighter`.

### Concept 04 — Data Cards
- **Palette:** Xám khói (Slate), Emerald, Rose (Đỏ cảnh báo).
- **Background:** `#F8FAFC`.
- **Đặc điểm:** Dùng chữ số làm decoration thay vì component đồ họa. Bố cục tự do, phá vỡ khung lưới Grid 12 truyền thống. Không có container "Card" bao bọc toàn bộ, mà dữ liệu đứng trực tiếp trên nền.
- **Bố cục chính:**
  - Hero KPI siêu to khổng lồ (`text-7xl`) góc trên bên trái.
  - Chuỗi bên phải dùng biểu đồ Bar phân mảnh (segmented bar).
  - Bảng "Nhân viên cần chú ý" sử dụng card hover tương phản.

### Concept 05 — Executive Monitor
- **Palette:** Trắng toàn tập, Xám nhạt, Xanh dương đậm / Đỏ làm điểm nhấn.
- **Background:** `#FFFFFF`.
- **Đặc điểm:** Sang trọng, cực kỳ tối giản (minimalist/executive). Giống một báo cáo in giấy trên bàn sếp. Loại bỏ hoàn toàn các khung viền, chỉ chia cách bằng divider line `border-b border-gray-100`.
- **Bố cục chính:**
  - Margin cực rộng `p-10 max-w-7xl mx-auto`.
  - 3 chỉ số chính nằm to ngang bằng nhau ở đầu trang.
  - Bố cục 3 cột (5-4-3) bên dưới, các dòng list không viền, đánh số nhỏ `01, 02` phong cách editorial.

## So Sánh
- **Clarity:** Concept 03 & 05 có độ nét và dễ đọc nhất do loại trừ decoration.
- **Premium Feel:** Concept 01 & 05.
- **Density:** Concept 03 nén được nhiều dữ liệu nhất trên một màn hình nhỏ. Concept 05 tốn nhiều không gian (whitespace) nhất.

Bạn có thể truy cập `/design-lab` trên menu sidebar để trực tiếp click qua lại giữa 5 concepts này mà không ảnh hưởng tới `/dashboard` production.
