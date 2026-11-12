import os



import sys



import re



import time



import threading
import hashlib



import logging



from typing import List, Dict, Any, Optional



from selenium import webdriver



from selenium.webdriver.common.by import By



from selenium.webdriver.common.keys import Keys



from selenium.webdriver.support.ui import WebDriverWait



from selenium.webdriver.support import expected_conditions as EC



from app.services.browser_manager import create_chrome_driver, cleanup_chrome_sessions



from app.config import get_config



logger = logging.getLogger(__name__)



def clean_zalo_message_text(text: str) -> str:



    """Lọc bỏ hoàn toàn các icon phản hồi, emotion, ký hiệu reaction của Zalo khỏi nội dung tin nhắn."""



    if not text:



        return ""



    # 1. Xóa các mã reaction của Zalo: /-strong, /-heart, /-rose, /-break, /-thanks...



    text = re.sub(r'/-(?:[a-zA-Z0-9_]+)', '', text)



    # 2. Xóa các ký hiệu emoticon Zalo: :>, :o, :-((, :-h, :), :( ...



    text = re.sub(r'(?m)^\s*(?::>|:o|:-\(\(|:-h|:-\)|:-\(|:\)|:\(|:D|:-D|:p|:-p|:v|:-v|;\))\s*$', '', text)



    # 3. Xóa số đếm reaction Zalo rớt lại ở cuối tin nhắn (chỉ xóa số nhỏ 1-9 lẻ loi ở dòng cuối cùng, TUYỆT ĐỐI không xóa mã shop 4-6 chữ số như 80623)
    text = re.sub(r'(?:\n\s*[1-9]\s*)+$', '', text)



    # 4. Xóa inline emoticon còn sót lại



    text = re.sub(r'(:>|:o|:-\(\(|:-h|/-(?:[a-zA-Z0-9_]+))', '', text)



    # 5. Xóa ký tự spacer 'a' vô hình ở đầu chuỗi do DOM của Zalo (ví dụ: 'a80165...' -> '80165...')



    text = re.sub(r'^a(?=[0-9])', '', text.strip())



    # 6. Chuẩn hóa khoảng trắng và dòng trống



    text = re.sub(r'\n\s*\n+', '\n', text)



    return text.strip()



def clean_sender_name(raw: str) -> str:



    """Tách lấy tên sạch của người gửi (loại bỏ text thừa, ký tự spacer và reaction)."""



    if not raw:



        return "Thành viên"



    lines = [line.strip() for line in raw.strip().split('\n') if line.strip()]



    valid_lines = [l for l in lines if l.lower() != 'a' and len(l) > 1]



    if valid_lines:



        first_line = clean_zalo_message_text(valid_lines[0])



        return first_line or "Thành viên"



    cleaned = clean_zalo_message_text(raw)



    return cleaned if (cleaned and cleaned.lower() != 'a') else "Thành viên"



def clean_time_string(raw: str, fallback: str = "") -> str:
    """
    Trích xuất ngày giờ gửi thực tế dạng DD/MM/YYYY HH:MM.
    Bảo toàn đầy đủ thông tin ngày và giờ.
    """
    if not raw:
        return fallback
    raw = raw.strip()

    # 1. Khớp ngày giờ đầy đủ DD/MM/YYYY HH:MM
    m_full = re.search(r'\b(\d{1,2}/\d{1,2}/\d{4}\s+(?:[01]?[0-9]|2[0-3]):[0-5][0-9])\b', raw)
    if m_full:
        return m_full.group(1)

    # 2. Khớp định dạng ISO: YYYY-MM-DD HH:MM
    m_iso = re.search(r'\b(\d{4}-\d{2}-\d{2}\s+(?:[01]?[0-9]|2[0-3]):[0-5][0-9])\b', raw)
    if m_iso:
        parts = m_iso.group(1).split(" ")
        dp = parts[0].split("-")
        return f"{dp[2]}/{dp[1]}/{dp[0]} {parts[1]}"

    # 3. Khớp chỉ có giờ HH:MM -> Tự động ghép ngày hôm nay
    m_time = re.findall(r'\b(?:[01]?[0-9]|2[0-3]):[0-5][0-9]\b', raw)
    if m_time:
        now_d = datetime.now().strftime("%d/%m/%Y")
        return f"{now_d} {m_time[-1]}"

    if len(raw) <= 25 and ":" in raw:
        return raw

    return fallback



class ZaloWebAdapter:



    def __init__(self):



        self.driver: Optional[webdriver.Chrome] = None



        self.profile_dir = os.path.join(



            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),



            "runtime",



            "zalo_web_profile"



        )



        self.is_monitoring = False



        self.active_group_name: Optional[str] = None



        self.seen_hashes = set()



        self.baseline_established = False
        self._lock = threading.Lock()
        self._is_opening = False
        self.is_headless = False



    def has_saved_session(self) -> bool:



        """Kiểm tra xem profile Chrome đã lưu cookie / session đăng nhập Zalo chưa."""



        if not os.path.exists(self.profile_dir):



            return False



        # Kiểm tra xem có file Cookies hoặc Local Storage / IndexedDB của Chrome hay không



        cookie_file = os.path.join(self.profile_dir, "Default", "Network", "Cookies")



        indexeddb_dir = os.path.join(self.profile_dir, "Default", "IndexedDB")



        return os.path.exists(cookie_file) or os.path.exists(indexeddb_dir)



    def is_chat_open(self) -> bool:



        """Kiểm tra xem khung chat (cuộc hội thoại) có đang được mở hiển thị trên Zalo Web không."""



        if not self.driver:



            return False



        try:



            # Kiểm tra tiêu đề header chat



            headers = self.driver.find_elements(



                By.CSS_SELECTOR, 



                "#chatViewHeader .header-title, .header-title, .chat-info-general__title, div[class*='header'] span[class*='title'], .title-name, .chat-name"



            )



            for h in headers:



                if h.is_displayed() and h.text.strip():



                    return True



            # Kiểm tra sự tồn tại của khung tin nhắn hoặc container chat



            chat_boxes = self.driver.find_elements(



                By.CSS_SELECTOR, 



                "#chatViewContainer, #messageViewContainer, #chat-box, .chat-view, .chat-content, div[class*='chat-message-list'], div[class*='message-view'], div.chat-item, div.bubble-content"



            )



            return len(chat_boxes) > 0 and any(cb.is_displayed() for cb in chat_boxes)



        except Exception:



            return False



    def get_active_header_title(self) -> str:
        """Lấy tên cuộc hội thoại hoặc nhóm chat đang hiển thị trên tiêu đề Zalo Web."""
        if not self.driver:
            return ""

        try:
            # 1. Trích xuất qua JavaScript (hoạt động tốt cả khi cửa sổ chạy ngầm hoặc unfocused)
            js_title = self.driver.execute_script("""
                try {
                    var selectors = [
                        '#chatViewHeader .header-title',
                        '#chatViewHeader [class*="header-title"]',
                        '#chatViewHeader [class*="title"]',
                        '#chatViewHeader .truncate',
                        '.chat-info-general__title',
                        '.chat-header .title',
                        '.title-name',
                        '.chat-name'
                    ];
                    for (var i = 0; i < selectors.length; i++) {
                        var el = document.querySelector(selectors[i]);
                        if (el) {
                            var t = (el.innerText || el.textContent || '').trim();
                            if (t && t.length > 0 && t.length < 120) {
                                return t.split(/[\r\n]+/)[0].trim();
                            }
                        }
                    }
                    var header = document.querySelector('#chatViewHeader, [data-id="chat-header"]');
                    if (header) {
                        var firstSpan = header.querySelector('span, div');
                        if (firstSpan) {
                            var t = (firstSpan.innerText || firstSpan.textContent || '').trim();
                            if (t && t.length > 0 && t.length < 100) return t.split(/[\r\n]+/)[0].trim();
                        }
                    }
                } catch(e) {}
                return '';
            """)
            if js_title and isinstance(js_title, str) and js_title.strip():
                return js_title.strip()
        except Exception:
            pass

        try:
            # 2. Fallback Selenium find_elements
            headers = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "#chatViewHeader .header-title, .header-title, .chat-info-general__title, div[class*='header'] span[class*='title'], .title-name, .chat-name"
            )
            for h in headers:
                try:
                    txt = (h.text or h.get_attribute("innerText") or "").strip()
                    if txt:
                        return txt
                except Exception:
                    continue
        except Exception:
            pass

        return ""

    def get_status(self) -> Dict[str, Any]:



        has_driver = self.driver is not None



        logged_in = False



        current_title = ""



        current_url = ""



        active_group = self.active_group_name



        if has_driver:



            try:



                current_url = self.driver.current_url



                current_title = self.driver.title



                if "chat.zalo.me" in current_url:



                    logged_in = len(self.driver.find_elements(By.CSS_SELECTOR, "#main-tab, .nav__tabs, #chat-box, .chat-view, .chat-info-general, div[id^='msg-']")) > 0



                



                # Cố gắng nhận diện tên cuộc hội thoại / Group đang mở trên màn hình



                detected_title = self.get_active_header_title()



                if detected_title:



                    active_group = detected_title



                    self.active_group_name = active_group



            except Exception:



                has_driver = False



                self.driver = None



        return {



            "browser_open": has_driver,
            "is_headless": getattr(self, "is_headless", False) if has_driver else False,



            "logged_in": logged_in,



            "is_monitoring": self.is_monitoring,



            "active_group": active_group,



            "current_title": current_title,



            "current_url": current_url



        }



    def open_browser(self, headless: bool = False) -> Dict[str, Any]:
        with self._lock:
            current_is_headless = getattr(self, "is_headless", False)
            if self.driver:
                try:
                    self.driver.current_url
                    if current_is_headless == headless:
                        if not headless:
                            # Tái sử dụng trình duyệt đang mở: kích hoạt và đưa cửa sổ Zalo lên phía trước
                            act_res = self.activate_window()
                            return act_res
                        return {"success": True, "action": "reused", "message": "Zalo Web đang chạy ngầm."}
                    mode_text = "Hiện cửa sổ quan sát" if not headless else "Ẩn vào nền (chạy ngầm)"
                    logger.info(f"Chuyển đổi chế độ Zalo Web: {mode_text}...")
                    try:
                        self.driver.quit()
                    except Exception:
                        pass
                    self.driver = None
                except Exception:
                    self.driver = None

            if self._is_opening:
                logger.info("Trình duyệt Zalo Web đang được khởi động bởi tiến trình khác, bỏ qua gọi trùng lặp.")
                return {"success": True, "action": "opening", "message": "Trình duyệt đang được khởi động..."}

            self._is_opening = True
            try:
                os.makedirs(self.profile_dir, exist_ok=True)
                cleanup_chrome_sessions(self.profile_dir)

                self.driver = create_chrome_driver(
                    profile_path=self.profile_dir,
                    headless=headless,
                    start_maximized=False if not headless else True,
                    app_url="https://chat.zalo.me" if not headless else None,
                    incognito=False,
                    isolated_profile=False
                )
                self.is_headless = headless

                if headless or not self.driver.current_url or "chat.zalo.me" not in self.driver.current_url.lower():
                    self.driver.get("https://chat.zalo.me")

                # Đóng các tab thừa nếu Chrome tự động mở thêm tab trống hoặc tab khôi phục
                try:
                    if len(self.driver.window_handles) > 1:
                        curr = self.driver.current_window_handle
                        for h in list(self.driver.window_handles):
                            if h != curr:
                                self.driver.switch_to.window(h)
                                if "chat.zalo.me" not in (self.driver.current_url or "").lower():
                                    self.driver.close()
                        self.driver.switch_to.window(curr)
                except Exception:
                    pass

                mode_str = "ngầm (headless)" if headless else "cửa sổ hiển thị (Chrome App Mode)"
                logger.info(f"Đã mở Zalo Web ở chế độ {mode_str}")

                # Khôi phục nhóm nếu trước đó đã chọn nhóm
                if self.active_group_name:
                    try:
                        time.sleep(1.2)
                        self.select_group(self.active_group_name)
                    except Exception:
                        pass

                act_res: Dict[str, Any] = {}
                if not headless:
                    time.sleep(0.5)
                    act_res = self.activate_window()

                return {
                    "success": True,
                    "action": "created",
                    "mode": "app" if not headless else "headless",
                    "message": act_res.get("message") if act_res else (
                        "Zalo Web đang chạy ngầm." if headless else "Đã mở Zalo Web ở chế độ App Mode."
                    ),
                    "activated": act_res.get("activated", True) if act_res else True
                }

            except Exception as e:
                logger.error(f"Lỗi khởi động trình duyệt Zalo Web: {e}", exc_info=True)
                self.driver = None
                raise
            finally:
                self._is_opening = False

    def activate_window(self) -> Dict[str, Any]:
        """Kích hoạt và đưa cửa sổ Zalo Web lên phía trước màn hình (Foreground)."""
        from app.services.window_activator import activate_zalo_window
        return activate_zalo_window(self.driver, self.profile_dir)

    def close_browser(self):
        with self._lock:
            self.is_monitoring = False
            if self.driver:
                try:
                    self.driver.quit()
                except Exception:
                    pass
                self.driver = None
            try:
                from app.services.browser_manager import cleanup_chrome_sessions
                cleanup_chrome_sessions(self.profile_dir)
            except Exception:
                pass
            logger.info("Đã đóng trình duyệt Zalo Web")

    def get_conversation_list(self) -> List[Dict[str, str]]:



        if not self.driver:



            return []



        conversations = []



        try:



            conv_items = self.driver.find_elements(By.CSS_SELECTOR, "div.conv-item, div[id^='conv-item-'], .conversation-item, div[data-id]")



            names = set()



            for item in conv_items:



                try:



                    title_els = item.find_elements(By.CSS_SELECTOR, ".conv-item-title__name, .conv-item-title, .truncate, div.name")



                    for el in title_els:



                        name = el.text.strip()



                        if any(name.startswith(p) for p in ['Bán:', 'Bạn:', 'Ban:', 'Hình ánh']):



                            continue



                        if '\n' in name:



                            name = name.split('\n')[0].strip()



                        if name and len(name) > 1 and name not in names:



                            names.add(name)



                            conversations.append({"name": name, "id": name})



                except Exception:



                    continue



            if not conversations:



                general_items = self.driver.find_elements(By.CSS_SELECTOR, ".conv-item-title__name")



                for it in general_items:



                    name = it.text.strip()



                    if name and len(name) > 1 and name not in names:



                        names.add(name)



                        conversations.append({"name": name, "id": name})



        except Exception as e:



            logger.warning(f"Lỗi lấy danh sách hội thoại: {e}")



        return conversations



    def select_group(self, group_name: str) -> bool:



        if not self.driver or not group_name:



            return False



        try:



            target_name = group_name.strip()



            # 1. Nếu khung chat đã và đang mở đúng nhóm này rồi thì không cần click lại



            current_header = self.get_active_header_title()



            if current_header and (target_name.lower() in current_header.lower() or current_header.lower() in target_name.lower()):



                self.active_group_name = current_header



                return True



            # 2. Thử tìm và click trực tiếp vào item hội thoại trong danh sách bên trái



            click_conv_js = """



            var target = arguments[0].toLowerCase();



            var items = document.querySelectorAll('div.conv-item, div.gridv2, div[id^="group-item-"], div[data-id], .conversation-item');



            for (var i = 0; i < items.length; i++) {



                var it = items[i];



                var t = (it.innerText || "").toLowerCase();



                if (t.indexOf(target) !== -1) {



                    var clickable = it.closest('div.conv-item, div.gridv2, div[id^="group-item-"]') || it;



                    clickable.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));



                    clickable.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));



                    clickable.dispatchEvent(new MouseEvent('click', {bubbles: true}));



                    clickable.click();



                    return true;



                }



            }



            return false;



            """



            clicked = self.driver.execute_script(click_conv_js, target_name)



            if clicked:



                time.sleep(1.2)



                active_h = self.get_active_header_title()



                if active_h and (target_name.lower() in active_h.lower() or active_h.lower() in target_name.lower()):



                    self.active_group_name = active_h



                    self.baseline_established = False



                    logger.info(f"Đã mở nhóm chat '{active_h}' từ danh sách bên trái.")



                    return True



            # 3. Nếu không thấy trong danh sách gần đây, sử dụng ô tìm kiếm của Zalo Web



            search_inputs = self.driver.find_elements(



                By.CSS_SELECTOR, 



                "#contact-search-input, input[placeholder*='Tìm kiếm'], input[placeholder*='Search'], .search-input, input.input-search"



            )



            if search_inputs:



                s_inp = None



                for inp in search_inputs:



                    if inp.is_displayed():



                        s_inp = inp



                        break



                if s_inp:



                    s_inp.click()



                    s_inp.clear()



                    for ch in target_name:



                        s_inp.send_keys(ch)



                        time.sleep(0.03)



                    time.sleep(1.2)



                    # Bấm vào kết quả item hội thoại trong danh sách tìm kiếm #searchResultList



                    click_search_res_js = """



                    var target = arguments[0].toLowerCase();



                    var list = document.querySelector('#searchResultList');



                    var container = list || document;



                    var items = container.querySelectorAll('div.conv-item, div.gridv2, div[id^="group-item-"]');



                    for (var i = 0; i < items.length; i++) {



                        var it = items[i];



                        var t = (it.innerText || "").toLowerCase();



                        if (t.indexOf(target) !== -1) {



                            var clickable = it.closest('div.conv-item, div.gridv2, div[id^="group-item-"]') || it;



                            clickable.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));



                            clickable.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));



                            clickable.dispatchEvent(new MouseEvent('click', {bubbles: true}));



                            clickable.click();



                            return true;



                        }



                    }



                    return false;



                    """



                    if self.driver.execute_script(click_search_res_js, target_name):



                        time.sleep(1.5)



                        active_h = self.get_active_header_title()



                        if active_h:



                            self.active_group_name = active_h



                            self.baseline_established = False



                            logger.info(f"Đã mở nhóm chat '{active_h}' từ kết quả tìm kiếm.")



                            return True



            # 4. Kiểm tra lại header nếu đang mở sẵn



            active_h = self.get_active_header_title()



            if active_h:



                self.active_group_name = active_h



                return True



            return False



        except Exception as e:



            logger.error(f"Không thể chọn nhóm {group_name}: {e}")



            return False



    def ensure_scrolled_to_bottom(self) -> bool:
        """
        Đảm bảo khung chat Zalo Web luôn được cuộn xuống tin nhắn mới nhất:
        1. Tự động tìm và bấm vào nút nổi 'Tin nhắn mới' / 'Xem tin mới' nếu Zalo Web bị khựng lại.
        2. Tự động cuộn các container chat xuống kịch đáy (scrollHeight).
        3. Phát sự kiện 'scroll' để kích hoạt Virtual DOM của Zalo render các tin nhắn mới nhất.
        """
        if not self.driver:
            return False
        try:
            scroll_to_bottom_script = """
            var scrolledAny = false;
            var maxDistance = 0;
            
            // 1. Tìm và bấm vào nút nổi 'Tin nhắn mới' / 'Scroll down'
            var newMsgSelectors = [
                '.bubble-unread',
                'div[class*="bubble-unread"]',
                'div[class*="new-message"]',
                'div[class*="new-msg"]',
                'div[class*="unread-banner"]',
                'div[class*="unread-bar"]',
                'div[class*="scroll-to-bottom"]',
                'div[class*="scroll-down"]',
                'div[class*="btn-scroll"]',
                '[data-id*="scroll-bottom"]',
                '[data-id*="unread-bubble"]',
                '.chat-scroll-bottom',
                'div[class*="chat-scroll-bottom"]'
            ];
            for (var i = 0; i < newMsgSelectors.length; i++) {
                var btns = document.querySelectorAll(newMsgSelectors[i]);
                for (var b = 0; b < btns.length; b++) {
                    try {
                        var btn = btns[b];
                        if (btn.offsetWidth > 0 || btn.offsetHeight > 0 || (btn.getClientRects && btn.getClientRects().length > 0)) {
                            btn.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
                            btn.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
                            btn.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                            btn.click();
                            scrolledAny = true;
                        }
                    } catch(e) {}
                }
            }

            // 2. Fallback tìm nút nổi theo chữ hiển thị (tiếng Việt & icon)
            var chatRoot = document.querySelector('#chatViewContainer, #chat-view, .chat-view, #chatView');
            if (chatRoot) {
                var allEls = chatRoot.querySelectorAll('span, div, button');
                for (var s = 0; s < allEls.length; s++) {
                    var elem = allEls[s];
                    if (elem.children.length <= 2) {
                        var txt = (elem.textContent || "").trim().toLowerCase();
                        if (txt === "tin nhắn mới" || txt === "có tin nhắn mới" || txt === "xem tin mới nhất" || txt === "tin mới") {
                            var clickable = elem.closest('button, div[role="button"]') || elem;
                            try {
                                clickable.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                clickable.click();
                                scrolledAny = true;
                            } catch(e) {}
                            break;
                        }
                    }
                }
            }

            // 3. Tự động ép thanh cuộn xuống sát đáy cho tất cả container có thể cuộn
            var candidates = document.querySelectorAll(
                '#messageViewContainer, .message-view__scroll, .transform-gpu, #chat-box, ' +
                '.chat-view, .chat-content, div[class*="chat-message-list"], div[class*="message-view"], ' +
                'div[class*="chat-body"], .chat-content-scroll, #chatViewContainer'
            );
            var containers = [];
            for (var i = 0; i < candidates.length; i++) {
                var el = candidates[i];
                if (el.scrollHeight > el.clientHeight + 10) {
                    containers.push(el);
                }
            }
            if (chatRoot) {
                var allDivs = chatRoot.querySelectorAll('div');
                for (var j = 0; j < allDivs.length; j++) {
                    var d = allDivs[j];
                    if (d.scrollHeight > d.clientHeight + 50) {
                        try {
                            var style = window.getComputedStyle(d);
                            if (style.overflowY === 'auto' || style.overflowY === 'scroll') {
                                if (containers.indexOf(d) === -1) containers.push(d);
                            }
                        } catch(e) {}
                    }
                }
            }

            for (var cIdx = 0; cIdx < containers.length; cIdx++) {
                var ct = containers[cIdx];
                var distFromBottom = ct.scrollHeight - ct.scrollTop - ct.clientHeight;
                if (distFromBottom > maxDistance) {
                    maxDistance = distFromBottom;
                }
                if (distFromBottom > 15) {
                    ct.scrollTop = ct.scrollHeight + 10000;
                    ct.dispatchEvent(new Event('scroll', { bubbles: true }));
                    scrolledAny = true;
                }
            }

            return { scrolled: scrolledAny, maxDistance: maxDistance };
            """
            result = self.driver.execute_script(scroll_to_bottom_script)
            if result and isinstance(result, dict):
                scrolled = result.get("scrolled", False)
                max_dist = result.get("maxDistance", 0)
                if scrolled:
                    sleep_time = 0.4 if max_dist > 500 else 0.25
                    time.sleep(sleep_time)
                return bool(scrolled)
            return False
        except Exception:
            return False

    def fetch_new_messages(self, include_history: bool = False, scroll_count: int = 0) -> List[Dict[str, Any]]:



        """



        Quét tin nhắn trong Group Chat.



        """



        if not self.driver:



            return []



        # Tự động lấy tên Group đang mở trên màn hình Zalo
        current_group = self.get_active_header_title()
        if current_group:
            self.active_group_name = current_group
        elif self.active_group_name:
            current_group = self.active_group_name
        else:
            cfg = get_config()
            current_group = cfg.get("zalo_monitor", {}).get("fixed_group_name") or "Zalo Group"
            self.active_group_name = current_group

        # Script bóc tách DOM sạch: Lấy nội dung tin nhắn thực, không bóc tách tên sender hay header container làm tin nhắn giả
        extract_script = """



        var messages = [];



        var chatRows = document.querySelectorAll('div.chat-item, div.msg-view, div[id^="msg-"]');



        var seenKeys = new Set();



        var lastSender = "\\u0054\\u0068\\u00e0\\u006e\\u0068\\u0020\\u0076\\u0069\\u00ea\\u006e";



        for (var i = 0; i < chatRows.length; i++) {



            var row = chatRows[i];



            



            var sender = "";



            var sEl = row.querySelector('.message-sender-name-content, .message-sender-name-bubble, .msg-header__name, .sender-name, span.author');



            if (sEl) {



                var sClone = sEl.cloneNode(true);



                var opEls = sClone.querySelectorAll('.opacity-0, [class*="opacity"]');



                for (var k = 0; k < opEls.length; k++) opEls[k].remove();



                if (sClone.innerText && sClone.innerText.trim()) {



                    var sLines = sClone.innerText.trim().split(String.fromCharCode(10));



                    for (var l = 0; l < sLines.length; l++) {



                        var sl = sLines[l].trim();



                        if (sl && sl.toLowerCase() !== 'a') {



                            sender = sl;



                            break;



                        }



                    }



                }



            }



            if (row.classList.contains('me') || row.querySelector('.me') || (row.className && row.className.indexOf('item--me') !== -1)) {



                sender = "\\u0054\\u00f4\\u0069";



            }



            if (!sender || sender.toLowerCase() === 'a') {



                sender = lastSender;



            } else {



                lastSender = sender;



            }



            var timeStr = "";

            // Strategy 0 (Chính xác tuyệt đối): Bóc tách timestamp 13 chữ số (milliseconds) từ DOM ID hoặc attribute của Zalo
            var tsMatch = row.innerHTML.match(/(?:bb_msg_id_|message-frame_|@)(\\d{13})/);
            if (!tsMatch && row.id) {
                tsMatch = row.id.match(/(\\d{13})/);
            }
            if (tsMatch) {
                try {
                    var dt = new Date(parseInt(tsMatch[1]));
                    if (!isNaN(dt.getTime())) {
                        var yyyy = dt.getFullYear();
                        var mo = ('0' + (dt.getMonth() + 1)).slice(-2);
                        var dd = ('0' + dt.getDate()).slice(-2);
                        var hh = ('0' + dt.getHours()).slice(-2);
                        var mm = ('0' + dt.getMinutes()).slice(-2);
                        timeStr = dd + '/' + mo + '/' + yyyy + ' ' + hh + ':' + mm;
                    }
                } catch(e) {}
            }

            // Strategy 1: Thẻ giờ chuyên biệt của Zalo Web
            if (!timeStr) {
                var tEl = row.querySelector('.card-send-time__sendTime, .card-send-time, .msg-time, [class*="sendTime"], [class*="send-time"], span[class*="time"], div[class*="time"]');
                if (tEl) {
                    var rawT = (tEl.textContent || "").trim();
                    var m1 = /(\\d{1,2}:\\d{2})/.exec(rawT);
                    if (m1) {
                        timeStr = m1[1];
                    } else {
                        var attrTitle = tEl.getAttribute('title') || "";
                        var mTitle = /(\\d{1,2}:\\d{2})/.exec(attrTitle);
                        if (mTitle) timeStr = mTitle[1];
                    }
                }
            }



            // Strategy 2: Quét tất cả thẻ con (span, div, small) có nội dung định dạng đúng giờ HH:MM (miễn nhiễm thay đổi CSS)

            if (!timeStr) {

                var smallEls = row.querySelectorAll('span, div, small');

                for (var si = 0; si < smallEls.length; si++) {

                    var st = (smallEls[si].textContent || "").trim();

                    if (st.length <= 8 && /^\\d{1,2}:\\d{2}$/.test(st)) {

                        timeStr = st;

                        break;

                    }

                }

            }



            // Strategy 3: Quét tất cả thuộc tính title trong row (tooltip gốc Zalo)

            if (!timeStr) {

                var titleEls = row.querySelectorAll('[title]');

                for (var k = 0; k < titleEls.length; k++) {

                    var tAttr = titleEls[k].getAttribute('title') || "";

                    var mt = /(\\d{1,2}:\\d{2})/.exec(tAttr);

                    if (mt) {

                        timeStr = mt[1];

                        break;

                    }

                }

            }



            // Strategy 4: Quét data attributes (data-time, data-timestamp, data-date, data-title)

            if (!timeStr) {

                var dataEls = row.querySelectorAll('[data-time], [data-timestamp], [data-date], [data-title]');

                for (var d = 0; d < dataEls.length; d++) {

                    var dVal = dataEls[d].getAttribute('data-time') || dataEls[d].getAttribute('data-title') || dataEls[d].getAttribute('data-date') || "";

                    var md = /(\\d{1,2}:\\d{2})/.exec(dVal);

                    if (md) {

                        timeStr = md[1];

                        break;

                    }

                }

            }



            // Đảm bảo timeStr luôn có đầy đủ ngày DD/MM/YYYY (quét từ date divider T6 23/10/2026, Hôm qua, Hôm nay nếu thiếu)
            if (timeStr && timeStr.indexOf('/') === -1) {
                var rowDate = "";
                var prev = row.previousElementSibling;
                while (prev) {
                    var pText = (prev.innerText || "").trim();
                    var pdMatch = pText.match(/(?:T[2-7]|CN)\\s+(\\d{1,2}\\/\\d{1,2}\\/\\d{4})/);
                    if (pdMatch) {
                        rowDate = pdMatch[1];
                        break;
                    }
                    var pdMatch2 = pText.match(/^(\\d{1,2}\\/\\d{1,2}\\/\\d{4})$/);
                    if (pdMatch2) {
                        rowDate = pdMatch2[1];
                        break;
                    }
                    if (pText.indexOf("Hôm qua") !== -1) {
                        var yd = new Date(Date.now() - 86400000);
                        rowDate = ('0' + yd.getDate()).slice(-2) + '/' + ('0' + (yd.getMonth() + 1)).slice(-2) + '/' + yd.getFullYear();
                        break;
                    }
                    if (pText.indexOf("Hôm nay") !== -1) {
                        var td = new Date();
                        rowDate = ('0' + td.getDate()).slice(-2) + '/' + ('0' + (td.getMonth() + 1)).slice(-2) + '/' + td.getFullYear();
                        break;
                    }
                    prev = prev.previousElementSibling;
                }
                if (!rowDate) {
                    var td2 = new Date();
                    rowDate = ('0' + td2.getDate()).slice(-2) + '/' + ('0' + (td2.getMonth() + 1)).slice(-2) + '/' + td2.getFullYear();
                }
                timeStr = rowDate + ' ' + timeStr;
            }

            // Bóc tách thông tin trích dẫn / phản hồi (Quote) trước khi xóa DOM



            var quoteObj = null;



            var qEl = row.querySelector('.message-quote-fragment__container, [class*="quote-fragment"], .quote-banner, [class*=\"quote-base\"], [class*=\"quote-container\"], .quote-banner, [class*="quote-base"], [class*="quote-container"]');



            if (qEl) {



                var qSender = "";



                var qAuthorEl = qEl.querySelector('.quote-name, .message-quote-fragment__title, .message-quote-fragment__title-wrapper, .message-quote-fragment__author, [class*="quote-name"], [class*="quote-author"], [class*="author"], strong, b');
                if (qAuthorEl && qAuthorEl.innerText) {
                    qSender = qAuthorEl.innerText.trim();
                }

                var qText = "";
                var qContentEl = qEl.querySelector('.message-quote-fragment__description, .message-quote-fragment__content, [class*="quote-description"], [class*="quote-content"], [class*="quote-text"], .quote-text, .quote-msg');
                if (qContentEl && qContentEl.innerText) {
                    qText = qContentEl.innerText.trim();
                } else {
                    var qClone = qEl.cloneNode(true);
                    var remAuth = qClone.querySelectorAll('.quote-name, .message-quote-fragment__title-wrapper, .message-quote-fragment__title, .message-quote-fragment__author, [class*="quote-author"], [class*="author"], strong, b');
                    for (var ri = 0; ri < remAuth.length; ri++) remAuth[ri].remove();
                    qText = qClone.innerText ? qClone.innerText.trim() : "";
                }
                if (qSender && qText && qText.toLowerCase().indexOf(qSender.toLowerCase()) === 0) {
                    qText = qText.substring(qSender.length).trim();
                }
                if (qText) {



                    quoteObj = {



                        sender: qSender,



                        text: qText



                    };



                }



            }



            var textEl = row.querySelector('.text-message__container, .message-content-render, .card--text, .bubble-content, .card-content');



            if (!textEl) {



                textEl = row;



            }



            var clone = textEl.cloneNode(true);



            var unwanted = clone.querySelectorAll(



                '.message-reaction-container, .reactions-container, .reacts-list, .react-icon-list, ' +



                '.message-quote-fragment__container, [class*="quote-fragment"], .quote-banner, [class*=\"quote-base\"], [class*=\"quote-container\"], ' +



                '.message-sender-name-wrapper, .message-sender-name-bubble, .message-sender-name-content-wrapper, .message-sender-name-content, ' +



                '.opacity-0, [class*="opacity-0"], .msg-header__name, .sender-name, ' +



                '.card-send-time, .card-send-time__sendTime, .msg-time, .chat-item__action, .context-menu'



            );



            for (var j = 0; j < unwanted.length; j++) {



                unwanted[j].remove();



            }



            var rawText = clone.innerText ? clone.innerText.trim() : "";



            if (!rawText || rawText.length < 2) continue;



            if (rawText === sender) continue;



            var qKey = quoteObj ? (quoteObj.sender + ":" + quoteObj.text) : "";



            var key = sender + "___" + rawText + "___" + qKey;



            if (seenKeys.has(key)) continue;



            seenKeys.add(key);



            messages.push({



                text: rawText,



                sender: sender,



                time: timeStr,



                quote: quoteObj



            });



        }



        // Backward pass: Trong Zalo Web khi gửi nhiều tin liên tiếp, Zalo chỉ render giờ ở tin CUỐI CÙNG của cụm.



        // Gán ngược thời gian từ tin cuối cụm lên các tin trước trong cùng cụm người gửi:



        for (var b = messages.length - 1; b >= 0; b--) {



            if (!messages[b].time && b + 1 < messages.length && messages[b+1].time && messages[b].sender === messages[b+1].sender) {



                messages[b].time = messages[b+1].time;



            }



        }



        // Forward pass: Gán xuôi thời gian cho các tin sau cùng người gửi



        for (var f = 1; f < messages.length; f++) {



            if (!messages[f].time && messages[f-1].time && messages[f].sender === messages[f-1].sender) {



                messages[f].time = messages[f-1].time;



            }



        }



        // Kế thừa theo lân cận nếu còn tin khuyết giờ



        var lastValidT = "";



        for (var k = 0; k < messages.length; k++) {



            if (messages[k].time) lastValidT = messages[k].time;



            else if (lastValidT) messages[k].time = lastValidT;



        }



        var firstValidT = "";



        for (var k = 0; k < messages.length; k++) {



            if (messages[k].time) { firstValidT = messages[k].time; break; }



        }



        if (firstValidT) {



            for (var k = 0; k < messages.length; k++) {



                if (!messages[k].time) messages[k].time = firstValidT;



                else break;



            }



        }



        return messages;



        """



        if include_history:



            collected_dict: Dict[str, Dict[str, Any]] = {}



            def _collect_current_dom():



                try:



                    raw_data = self.driver.execute_script(extract_script) or []



                    for item in raw_data:



                        text = item.get("text", "").strip()



                        text = clean_zalo_message_text(text)



                        if not text or len(text) < 2:



                            continue



                        sender = clean_sender_name(item.get("sender"))



                        sent_time = clean_time_string(item.get("time"), fallback="")



                        quote_data = item.get("quote")



                        if quote_data and isinstance(quote_data, dict):



                            q_text = clean_zalo_message_text(quote_data.get("text", ""))



                            q_sender = clean_sender_name(quote_data.get("sender", ""))



                            if q_sender and q_text.lower().startswith(q_sender.lower()):
                                q_text = q_text[len(q_sender):].strip()
                            quote_data = {"sender": q_sender, "text": q_text} if q_text else None



                        else:



                            quote_data = None



                        q_hash_part = quote_data["text"] if quote_data else ""



                        m_hash = hashlib.sha256(f"{current_group}_{sender}_{text}_{q_hash_part}".encode("utf-8")).hexdigest()



                        if m_hash not in collected_dict:



                            collected_dict[m_hash] = {



                                "hash": m_hash,



                                "group_name": current_group,



                                "sender": sender,



                                "content": text,



                                "time_str": sent_time,



                                "quote": quote_data



                            }



                except Exception as ex:



                    logger.warning(f"Lỗi extract DOM: {ex}")



            # 1. Bóc tách vị trí ban đầu (tin mới ở đáy)



            _collect_current_dom()



            # 2. Vừa cuộn ngược lên vừa bóc tách tích lũy (không bị mất do virtual DOM unmount)



            scroll_script = """



            var containers = document.querySelectorAll('#messageViewContainer, .message-view__scroll, .transform-gpu, #chat-box, .chat-view, .chat-content, div[class*="chat-message-list"], div[class*="message-view"], div[class*="chat-body"], .chat-content-scroll, #chatViewContainer');



            var didScroll = false;



            for (var i = 0; i < containers.length; i++) {



                var c = containers[i];



                if (c.scrollHeight > c.clientHeight && c.scrollTop > 0) {



                    c.scrollTop = Math.max(0, c.scrollTop - 750);



                    didScroll = true;



                }



            }



                        if (!didScroll) {



                window.scrollBy(0, -750);



            }



            return didScroll;



            """



            sleep_time = 0.35 if scroll_count >= 50 else (0.45 if scroll_count >= 20 else 0.6)



            no_scroll_count = 0



            for step in range(scroll_count):



                try:



                    scrolled = self.driver.execute_script(scroll_script)



                    if not scrolled:



                        no_scroll_count += 1



                        if no_scroll_count >= 4:



                            logger.info(f"Đã chạm đỉnh lịch sử chat (sau {step+1} lần cuộn), dừng cuộn sớm.")



                            break



                    else:



                        no_scroll_count = 0



                except Exception:



                    pass



                time.sleep(sleep_time)



                _collect_current_dom()



            # Cuộn lại về đáy sau khi quét lịch sử



            restore_scroll = """



            var containers = document.querySelectorAll('#messageViewContainer, .message-view__scroll, .transform-gpu, #chat-box, .chat-view, .chat-content');



            for (var i = 0; i < containers.length; i++) {



                var c = containers[i];



                if (c.scrollHeight > c.clientHeight) {



                    c.scrollTop = c.scrollHeight;



                }



            }



            """



            try:



                self.driver.execute_script(restore_scroll)



            except Exception:



                pass



            logger.info(f"Đã quét lịch sử (cuộn {scroll_count} lần), tích lũy được {len(collected_dict)} tin nhắn từ Group '{current_group}'.")



            return list(collected_dict.values())



        # Chế độ giám sát đón tin mới thông thường



        new_messages = []



        try:



            # 1. Trích xuất những tin nhắn hiện đang có trên màn hình trước
            pre_raw = self.driver.execute_script(extract_script) or []

            # 2. Tự động ép cuộn xuống kịch đáy và bấm nút nổi 'Tin nhắn mới' nếu bị khựng
            did_scroll = self.ensure_scrolled_to_bottom()

            # 3. Trích xuất tiếp các tin nhắn ở đáy mới nhất (gộp và tự động khử trùng bằng hash)
            if did_scroll:
                post_raw = self.driver.execute_script(extract_script) or []
                raw_data = pre_raw + post_raw
            else:
                raw_data = pre_raw



            current_hashes = []



            extracted_items = []



            for item in raw_data:



                text = item.get("text", "").strip()



                text = clean_zalo_message_text(text)



                if not text or len(text) < 2:



                    continue



                sender = clean_sender_name(item.get("sender"))



                sent_time = clean_time_string(item.get("time"), fallback=time.strftime("%d/%m/%Y %H:%M"))



                quote_data = item.get("quote")



                if quote_data and isinstance(quote_data, dict):



                    q_text = clean_zalo_message_text(quote_data.get("text", ""))



                    q_sender = clean_sender_name(quote_data.get("sender", ""))



                    if q_sender and q_text.lower().startswith(q_sender.lower()):
                        q_text = q_text[len(q_sender):].strip()
                    quote_data = {"sender": q_sender, "text": q_text} if q_text else None



                else:



                    quote_data = None



                q_hash_part = quote_data["text"] if quote_data else ""



                m_hash = hashlib.sha256(f"{current_group}_{sender}_{text}_{q_hash_part}".encode("utf-8")).hexdigest()



                current_hashes.append(m_hash)



                extracted_items.append({



                    "hash": m_hash,



                    "group_name": current_group,



                    "sender": sender,



                    "content": text,



                    "time_str": sent_time,



                    "quote": quote_data



                })



            # Đồng bộ seen_hashes từ database để không quét trùng và KHÔNG làm mất tin nhắn mới
            try:
                from app.services.zalo_db import get_all_msg_hashes
                db_hashes = get_all_msg_hashes()
                if db_hashes:
                    self.seen_hashes.update(db_hashes)
            except Exception:
                pass

            # Chỉ thiết lập baseline bỏ qua màn hình NẾU database hoàn toàn trống
            if not self.baseline_established and len(self.seen_hashes) == 0:
                for h in current_hashes:
                    self.seen_hashes.add(h)
                self.baseline_established = True
                logger.info(f"Đã thiết lập baseline {len(self.seen_hashes)} tin nhắn ban đầu trong group '{current_group}'.")
                return []

            self.baseline_established = True
            for it in extracted_items:



                if it["hash"] not in self.seen_hashes:



                    self.seen_hashes.add(it["hash"])



                    new_messages.append(it)



        except Exception as e:



            logger.warning(f"Lỗi quét tin nhắn Group Zalo Web: {e}")



        return new_messages



# Singleton instance



zalo_web_adapter = ZaloWebAdapter()



