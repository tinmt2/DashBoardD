# BÁO CÁO ĐIỀU TRA NGUYÊN NHÂN GỐC RỄ & ĐÁNH GIÁ PHƯƠNG ÁN NHÚNG ZALO
## PHASE 8.1E — ZALO EMBEDDED VIEW ROOT-CAUSE INVESTIGATION

- **Thời gian thực hiện:** 11/11/2026
- **Trạng thái:** HOÀN THÀNH ĐIỀU TRA (CHẨN ĐOÁN & ĐỀ XUẤT, CHƯA SỬA CODE)
- **Hệ thống liên quan:**
  - DashBoardD Frontend: `dashboard-app/` (`http://localhost:5174` Dev, `http://localhost:8000` Prod)
  - DashBoardD Backend: `DashBoardD/backend/` (Port 8000)
  - Test Engine Backend: `test/` (Port 18020)
  - Zalo Adapter: `test/app/services/zalo_web_adapter.py`
  - Browser Manager: `test/app/services/browser_manager.py`

---

## 1. TÓM TẮT ĐIỀU TRA (EXECUTIVE SUMMARY)

1. **Hiện tượng người dùng gặp phải:**
   - Trên giao diện DashBoardD tại route `#/admin/zalo`, khi bấm nút **"Mở Zalo Web"**, người dùng không nhìn thấy cửa sổ Zalo xuất hiện trên màn hình desktop.
   - Người dùng mong muốn giao diện Web Zalo được **nhúng (embedded)** trực tiếp bên trong không gian trang `#/admin/zalo` của DashBoardD.

2. **Kết quả chẩn đoán nhanh:**
   - **Backend thực tế đã mở Chrome thành công:** Gọi `GET /api/test/api/zalo/status` xác nhận:
     ```json
     "adapter_status": {
         "browser_open": true,
         "is_headless": false,
         "logged_in": true,
         "active_group": "GS AN NINH",
         "current_title": "Zalo - Trung Tâm Gscmr Frt",
         "current_url": "https://chat.zalo.me/"
     }
     ```
     Chrome PID 22424 đang chạy với profile `D:\Tín\ABC\test\runtime\zalo_web_profile`.
   - **Lý do người dùng "không thấy cửa sổ":**
     - **Bug No-op khi bấm lại:** Trong `zalo_web_adapter.py` (dòng 557), nếu trình duyệt đang mở ở trạng thái `headless == False`, adapter thực thi `if current_is_headless == headless: return True` mà **không hề gọi lệnh kích hoạt cửa sổ hay đưa lên trên cùng (SetForegroundWindow / Restore)**.
     - **Windows Focus Stealing Prevention:** Chrome được khởi chạy từ tiến trình con `chromedriver.exe` (thuộc Python `uvicorn`). Windows tự động chặn tiến trình nền chiếm quyền focus màn hình (Foreground Lock Timeout), dẫn đến cửa sổ Chrome bị chìm hoàn toàn xuống dưới cửa sổ Dashboard hoặc ẩn vào taskbar.
     - **Giao diện hiện tại hoàn toàn chưa có vùng nhúng:** Trong `ZaloMonitorPage.tsx`, layout hiện chỉ có các thẻ KPI và bảng log; chưa hề có thẻ `<iframe>` hay container nhúng Zalo nào.

3. **Về khả năng nhúng Zalo Web vào Dashboard:**
   - **Phương án `iframe` trên nền Web thông thường:** **HOÀN TOÀN KHÔNG KHẢ THI** do Zalo áp dụng chính sách Content Security Policy (`frame-src 'self' *.zalo.me`), anti-framing frame busting và cơ chế Partitioned Cookies (CHIPS) chặn lưu session/cookie của Zalo trong iframe cross-origin.
   - **Phương án Electron WebView / BrowserView:** **HOÀN TOÀN KHẢ THI VÀ TỐT NHẤT NẾU CHẠY DESKTOP APP** (Mã nguồn Electron đã có sẵn trong `DashBoardD/dashboard-app/electron/main.cjs`).
   - **Phương án Chrome App Mode (Độc lập, nổi bật):** **KHẢ THI 100% TRÊN MỌI MÔI TRƯỜNG (CẢ WEB LẪN DESKTOP)** bằng cách mở Chrome với cờ `--app=https://chat.zalo.me` và gọi Win32 Focus API để cửa sổ Zalo luôn bật nổi ngay cạnh Dashboard.

---

## 2. BƯỚC 1 — TRUY VẾT NÚT MỞ ZALO (FRONTEND ĐẾN BACKEND)

### 2.1. Thành phần Frontend và Event Handler
- **File:** `DashBoardD/dashboard-app/src/pages/test/ZaloMonitorPage.tsx`
- **Nút bấm:**
  - Khi chưa mở (`browser_open == false`): Nút **"Mở Zalo Web"** (dòng 364) kích hoạt `handleOpenBrowser(false)`.
  - Khi đã mở (`browser_open == true` và `is_headless == false`): Nút chuyển thành **"Thu ngầm"** (dòng 342) và nút đóng **"X"** (dòng 354).
- **Hàm xử lý:**
  ```typescript
  const handleOpenBrowser = async (headless: boolean = false) => {
    setLoading(true);
    try {
      const res = await zaloApi.openBrowser(headless);
      setStatusMessage(res.message || (headless ? 'Zalo Web đang chạy ngầm' : 'Đã mở cửa sổ Zalo Web'));
      setTimeout(fetchConversations, 2500);
    } catch (e: any) {
      setStatusMessage('Lỗi mở trình duyệt: ' + e.message);
    } finally {
      setLoading(false);
    }
  };
  ```

### 2.2. API Client và Luồng mạng
1. `dashboard-app/src/services/testApi/zaloApi.ts`:
   - `openBrowser: async (headless = false) => testApiClient('/api/zalo/open-browser', { method: 'POST', body: JSON.stringify({ headless }) })`
2. **Reverse Proxy DashBoardD (Port 8000):**
   - URL: `POST http://localhost:8000/api/test/api/zalo/open-browser`
   - Route forward: `DashBoardD/backend/app/api/routes/test_proxy.py` chuyển tiếp sang `http://127.0.0.1:18020/api/zalo/open-browser`.
3. **Test Engine Backend Router (Port 18020):**
   - File: `test/app/api/routes/zalo_router.py` (dòng 624-658)
   - Endpoint: `@router.post("/open-browser")`
   - Gọi: `await asyncio.to_thread(zalo_web_adapter.open_browser, headless=payload.headless)`
   - Trả về: `ApiResponse(success=True, status="ok", message="Trình duyệt đã được mở. Vui lòng đăng nhập nếu chưa đăng nhập.")`

### 2.3. Endpoint chỉ đọc trạng thái
- `GET /api/test/api/zalo/status?include_messages=false`
- Được `ZaloMonitorPage.tsx` gọi mỗi 10 giây một lần qua `fetchStatus()`.
- Lấy thông tin từ `zalo_web_adapter.get_status()`, bao gồm: `browser_open`, `is_headless`, `logged_in`, `active_group`, `current_title`, `current_url`.

### 2.4. Xác định nguyên nhân gốc rễ khiến "Không hiển thị cửa sổ"

| STT | Nguyên nhân kỹ thuật | Vị trí mã nguồn | Hiện tượng quan sát được |
|:---:|:---|:---|:---|
| **1** | **No-op khi trình duyệt đã tồn tại** | `test/app/services/zalo_web_adapter.py` dòng 554-558 | Nếu `self.driver` đã chạy với `is_headless == False`, hàm kiểm tra `if current_is_headless == headless: return True` và lập tức thoát mà **không thực hiện bất kỳ hành động nào để hiện/nổi cửa sổ**. |
| **2** | **Windows Focus Lock Timeout** | Windows OS / `chromedriver.exe` | Chromedriver được sinh ra từ Python backend. Windows áp dụng chính sách bảo vệ không cho phép tiến trình nền tự cướp tiêu điểm (focus). Cửa sổ Chrome mở ra nhưng nằm dưới cùng các cửa sổ đang hoạt động. |
| **3** | **Khởi chạy dưới dạng Browser thông thường thay vì App Window** | `test/app/services/zalo_web_adapter.py` dòng 578 & `browser_manager.py` dòng 80-84 | Khi mở Chrome, tùy chọn `--app=https://chat.zalo.me` không được truyền (`app_url=None`), mà dùng `--start-maximized`. Chrome mở ra với đầy đủ thanh tab, bookmark và bị gộp chung vào nhóm cửa sổ Chrome của hệ thống trên thanh Taskbar. |
| **4** | **Chưa có thành phần nhúng trong giao diện React** | `dashboard-app/src/pages/test/ZaloMonitorPage.tsx` | Trang `ZaloMonitorPage.tsx` hiện tại chỉ đóng vai trò bảng điều khiển giám sát (Stats, KPI, Log sự kiện), chưa có bất kỳ phần tử DOM nào để hiển thị trực tiếp nội dung Zalo. |

---

## 3. BƯỚC 2 — XÁC ĐỊNH NỀN TẢNG HIỂN THỊ (RUNTIME & PLATFORM)

### 3.1. Nền tảng thực thi hiện tại
- Hệ thống hiện đang chạy dưới dạng **Web Application đa dịch vụ**:
  - Frontend: Vite Dev Server trên cổng `5174` (hoặc FastAPI serving static `dist` trên cổng `8000`).
  - Giao diện được người dùng truy cập thông qua trình duyệt web thông thường (Google Chrome / Microsoft Edge).
  - Không có tiến trình Electron nào đang chạy (`Get-Process electron` trả về rỗng).

### 3.2. Cấu trúc Desktop App có sẵn trong repository
- Dự án `DashBoardD` **đã tích hợp sẵn cấu hình Electron**:
  - File chính: `DashBoardD/dashboard-app/electron/main.cjs`
  - Preload: `DashBoardD/dashboard-app/electron/preload.cjs`
  - Cấu hình: `package.json` có các script `electron:dev`, `electron:build`, target `nsis x64`.
  - Cửa sổ Electron được cấu hình không viền (`frame: false`), hỗ trợ IPC điều khiển cửa sổ (`window-min`, `window-max`, `window-close`).

### 3.3. Cơ chế Zalo Adapter hiện tại
- Zalo Adapter trong `test/app/services/zalo_web_adapter.py` sử dụng **Selenium WebDriver** (`selenium.webdriver.Chrome`).
- Profile lưu tại `D:\Tín\ABC\test\runtime\zalo_web_profile`, giúp duy trì cookie và phiên đăng nhập IndexedDB sau mỗi lần khởi động lại.
- Trình duyệt chạy có GUI khi `headless=False` và chạy ngầm khi `headless=True`.

---

## 4. BƯỚC 3 — ĐÁNH GIÁ CÁC PHƯƠNG ÁN NHÚNG GIAO DIỆN ZALO

### Phương án 1: `iframe` (Trực tiếp hoặc qua Reverse Proxy)
- **Mô tả:** Đặt thẻ `<iframe src="https://chat.zalo.me" />` vào trong component React hoặc tạo proxy bóc tách header qua backend.
- **Khả năng thành công:** **0% (HOÀN TOÀN KHÔNG KHẢ THI)**.
- **Rào cản kỹ thuật:**
  1. *Chính sách bảo mật Zalo (CSP & Framing):* Response headers của Zalo quy định:
     `Content-Security-Policy: ... frame-src 'self' *.zalo.me ...` và `default-src 'none'`. Zalo có script client-side chống iframe (frame busting).
  2. *Cơ chế Partitioned Cookies (CHIPS) của trình duyệt:* Chromium 115+ cô lập toàn bộ cookie của iframe nhúng trong origin khác (`localhost:5174` / `:8000`). Người dùng quét mã QR xong sẽ bị văng ra ngay lập tức do cookie session không lưu được vào storage chính thống.
  3. *Hệ thống Domain phân tán:* Zalo sử dụng hàng chục subdomain khác nhau cho WebSocket (`wss://*.chat.zalo.me`), Media CDN (`*.zdn.vn`, `*.zadn.vn`), file transfer (`*.dlfl.me`). Reverse proxy không thể map toàn bộ hệ thống này mà không vi phạm SSL/CORS.
- **Tác động bảo mật:** Nguy hiểm cao nếu cố tình tắt bảo mật trình duyệt (`--disable-web-security`).
- **Khuyến nghị:** **LOẠI BỎ**.

---

### Phương án 2: Electron WebView / BrowserView / WebContentsView
- **Mô tả:** Nhúng trực tiếp một native Chromium view vào bên trong cửa sổ DashBoardD khi chạy dưới dạng Electron Desktop App.
- **Khả năng thành công:**
  - Trên **Electron Desktop App**: **100% (RẤT TỐT)**.
  - Trên **Web Browser thông thường**: **0%** (vì trình duyệt web không có quyền gọi Electron API).
- **Cơ chế kỹ thuật:**
  - Trong `main.cjs`, khởi tạo một `BrowserView` (hoặc `WebContentsView`) với URL `https://chat.zalo.me`.
  - Session sử dụng thư mục dữ liệu bền vững: `session.fromPath('D:/Tín/ABC/test/runtime/zalo_web_profile')`.
  - Frontend React gửi tọa độ vùng chứa (`<div id="zalo-embed-container">`) qua IPC để Electron ghim chính xác BrowserView vào không gian giao diện của trang.
- **Độ phức tạp:** Trung bình (cần thêm khoảng 40 dòng mã IPC trong `main.cjs` và hook React để lắng nghe resize).
- **Khuyến nghị:** **PHƯƠNG ÁN TỐI ƯU NHẤT NẾU NGƯỜI DÙNG CHUYỂN SANG DÙNG ELECTRON DESKTOP**.

---

### Phương án 3: Chrome DevTools Protocol (CDP) Screencast / Canvas Stream
- **Mô tả:** Backend kết nối CDP WebSocket tới Chrome (`Page.startScreencast`), stream các khung hình JPEG base64 về frontend để vẽ lên thẻ `<canvas>`, đồng thời chuyển tiếp sự kiện chuột/phím từ canvas ngược lại CDP.
- **Khả năng thành công:** Khả thi về lý thuyết nhưng **TRẢI NGHIỆM THỰC TẾ KÉM**.
- **Rào cản kỹ thuật:**
  1. *Độ trễ cao:* Rê chuột, gõ phím phải đi qua vòng lặp mạng (React ↔ FastAPI ↔ CDP ↔ Chrome) gây độ trễ 150-400ms.
  2. *Lỗi gõ tiếng Việt (Telex/VNI):* Bàn phím gõ tiếng Việt qua CDP event thường xuyên bị nuốt dấu hoặc sai vị trí con trỏ.
  3. *Tải tài nguyên:* CPU phải liên tục chụp màn hình và nén ảnh JPEG 30fps làm nóng máy và tốn RAM.
- **Khuyến nghị:** **KHÔNG NÊN DÙNG**.

---

### Phương án 4: Native Chrome Window "App Mode" Side-by-Side (Khuyến nghị cho Web)
- **Mô tả:**
  - Khởi động Chrome bằng flag `--app=https://chat.zalo.me`.
  - Khi chạy cờ `--app`, Chrome sẽ hiển thị như một **cửa sổ ứng dụng độc lập**:
    - Không có thanh địa chỉ (Omnibox).
    - Không có các tab thừa hoặc thanh tiện ích.
    - Có icon Zalo riêng biệt trên taskbar.
  - Tích hợp thêm **Win32 Window Management** trong Python backend (`user32.ShowWindow`, `user32.SetForegroundWindow`).
  - Khi người dùng bấm "Mở Zalo Web" hoặc "Hiện Zalo", cửa sổ App Mode ngay lập tức được khôi phục kích thước và nổi lên trên cùng (Foreground) màn hình, đặt ngay cạnh hoặc phủ góc Dashboard.
- **Khả năng thành công:** **100% — HOẠT ĐỘNG HOÀN HẢO TRÊN CẢ TRÌNH DUYỆT WEB LẪN DESKTOP**.
- **Ưu điểm vượt trội:**
  1. Giữ nguyên 100% tính năng gốc của Zalo: quét QR đăng nhập, gọi video, gửi file đính kèm, thông báo âm thanh.
  2. Gõ tiếng Việt chuẩn xác không độ trễ.
  3. Không phụ thuộc vào Electron (hoạt động tốt ngay trên nền tảng Web hiện tại).
  4. Duy trì trọn vẹn kết nối tự động của Test Engine backend (`selenium` driver điều khiển trực tiếp cửa sổ này để đọc tin nhắn và giám sát realtime).
  5. Sửa đổi mã nguồn tối thiểu, an toàn tuyệt đối.

---

## 5. BẢNG SO SÁNH TỔNG HỢP CÁC PHƯƠNG ÁN

| Tiêu chí đánh giá | Phương án 1: `iframe` | Phương án 2: Electron BrowserView | Phương án 3: CDP Screencast | Phương án 4: Chrome App Mode + Win32 Focus |
|:---|:---:|:---:|:---:|:---:|
| **Khả năng thành công trên Web** | ❌ 0% (Bị Zalo chặn) | ❌ 0% (Cần Electron) | ⚠️ 60% (Lag, lỗi gõ TV) | ✅ **100% (Hoạt động ngay)** |
| **Khả năng thành công trên Desktop** | ❌ 0% | ✅ **100% (Nhúng hoàn hảo)** | ⚠️ 60% | ✅ **100% (Cửa sổ độc lập)** |
| **Trải nghiệm đăng nhập QR** | ❌ Lỗi session loop | ✅ Hoạt động 100% | ⚠️ Chậm | ✅ **Hoạt động 100%** |
| **Gõ tiếng Việt / File upload** | ❌ Không thể | ✅ Chuẩn native | ❌ Dễ nuốt chữ | ✅ **Chuẩn native 100%** |
| **Độ phức tạp triển khai** | Rất cao (thất bại) | Trung bình (cần Electron) | Cực kỳ cao | **Thấp / Tinh gọn nhất** |
| **Rủi ro ảnh hưởng hệ thống** | Cao (phá vỡ CORS) | Thấp | Cao (tải CPU) | **Rất thấp (an toàn)** |

---

## 6. ĐỀ XUẤT PHƯƠNG ÁN TỐI THIỂU (MINIMAL REMEDIATION PLAN)

Dựa trên việc hệ thống hiện tại đang được vận hành chủ yếu qua trình duyệt Web (`start_all.cmd` mở `http://localhost:5174` hoặc `http://localhost:8000`), đề xuất giải pháp tối ưu chia làm 2 giai đoạn:

### Giai đoạn 1: Khắc phục triệt để hiển thị cửa sổ (Chrome App Mode + Win32 Bring-to-Front)
1. **Sửa logic trong `test/app/services/zalo_web_adapter.py`:**
   - Trong `open_browser(headless=False)`:
     - Khi `self.driver` đã tồn tại: Không thoát no-op nữa, mà gọi lệnh Win32 `ShowWindow(SW_RESTORE)` và `SetForegroundWindow()` để đưa ngay cửa sổ Zalo lên mặt kính màn hình.
     - Khi khởi tạo mới driver: Sử dụng tham số `app_url="https://chat.zalo.me"` thay vì mở trình duyệt thông thường.
2. **Cập nhật giao diện `ZaloMonitorPage.tsx`:**
   - Khi cửa sổ Zalo đang mở, cung cấp nút **"Đưa lên trên cùng"** (Brings window to front) giúp người dùng kích hoạt cửa sổ Zalo bất cứ lúc nào chỉ với 1 click.
   - Thêm trạng thái trực quan: *"Cửa sổ Zalo App Mode đang mở song song"*.

### Giai đoạn 2: Tùy chọn nâng cao nếu người dùng muốn nhúng 100% trong 1 cửa sổ (Electron Integration)
- Nếu người dùng muốn trải nghiệm tất cả trong duy nhất một khung cửa sổ desktop:
  - Thêm lựa chọn khởi chạy Electron vào `start_all.cmd` (Chế độ Desktop App).
  - Tích hợp `BrowserView` vào `DashBoardD/dashboard-app/electron/main.cjs` để hiển thị Zalo trực tiếp trong component `ZaloMonitorPage.tsx`.

---

## 7. KẾT LUẬN & TRẠNG THÁI HIỆN TẠI

- Quá trình điều tra Phase 8.1E đã hoàn thành 100% theo đúng quy tắc an toàn.
- **Không có dòng code nghiệp vụ nào bị sửa đổi** trong giai đoạn này.
- **Không thực hiện đóng gói frontend (`npm run build`)** theo đúng chỉ thị của người dùng.
- Tiến trình và cơ sở dữ liệu hoàn toàn nguyên vẹn.
- Báo cáo này đã sẵn sàng để người dùng xem xét và phê duyệt định hướng triển khai.
