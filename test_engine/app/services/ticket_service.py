from __future__ import annotations

import re

MAP_LONG_CHAU = {
    "miền bắc 1": "Miền Bắc 1 -LC",
    "miền bắc 2": "Miền Bắc 2_LC",
    "miền đông": "Miền Đông_LC",
    "miền đông nam bộ": "Miền Đông Nam Bộ-LC",
    "hồ chí minh": "Hồ Chí Minh-LC",
    "hồ chí minh 1": "Hồ Chí Minh-LC",
    "hồ chí minh 2": "Hồ Chí Minh 2-LC",
    "hà nội": "Hà Nội-LC",
    "miền trung": "Miền Trung-LC",
    "miền tây": "Miền Tây Nam Bộ-LC",
    "miền tây nam bộ": "Miền Tây Nam Bộ-LC",
}

MAP_FPT_SHOP = {
    "miền bắc 1": "Miền Bắc 1",
    "miền bắc 2": "Miền Bắc 2",
    "miền bắc 3": "Miền Bắc 3",
    "miền đông": "Miền Đông Nam Bộ 1",
    "miền đông 1": "Miền Đông Nam Bộ 1",
    "miền đông 2": "Miền Đông Nam Bộ 2",
    "hồ chí minh": "Hồ Chí Minh",
    "hà nội": "Hà Nội",
    "miền trung": "Miền Trung",
    "miền tây": "Miền Tây Nam Bộ",
}

CREATE_URL = "https://ssc.fptshop.com.vn/secure/SSC01CreateTicket.jspa?processId=232"

# Selectors
ID_SUBJECT = "sms-ticket-title-real"
NAME_SUBJECT = "Request Subject"
ID_LOCATION_CONTAINER = "s2id_sms-ticket-location"
XPATH_TEXTAREA = "//textarea[@name='Nội Dung Cần Hỗ Trợ']"
ID_SUBMIT = "add-ticket-submit"
XPATH_SUBMIT_GZ = "//*[@id='add-ticket-submit'] | //a[contains(@class, 'btn') and contains(text(), 'Gửi')] | //button[@type='submit' or contains(@class, 'submit')]"
XPATH_SUBMIT_GENERIC = "//button[@type='submit']"
ID_VIEW_TICKET = "view-ticket"


def convert_location(raw_loc: str, sys_mode: str) -> str:
    val = str(raw_loc).strip()
    key = val.lower()
    if key in MAP_LONG_CHAU:
        return MAP_LONG_CHAU[key]
    if key in MAP_FPT_SHOP:
        return MAP_FPT_SHOP[key]

    if sys_mode == "LC":
        if not key.endswith("lc") and "-lc" not in key:
            return f"{val}-LC"
    return val


def normalize_camera(raw_cam: str) -> str:
    val = str(raw_cam).strip()
    if not val:
        return ""
    
    # Try to extract number
    m = re.search(r"(\d+)", val)
    if m:
        num = int(m.group(1))
        return f"CH{num:02d}"
    
    # Fallback for non-numeric cases (e.g. "Cam X")
    if val.lower().startswith("camera"):
        val = val[6:].strip()
    elif val.lower().startswith("cam"):
        val = val[3:].strip()
    elif val.lower().startswith("ch"):
        val = val[2:].strip()
    
    return f"CH{val}" if val else "CH"


def build_subject(ma_shop: str, ten_shop: str, camera_text: str, is_dvr: bool, is_no_data: bool = False, is_hdd: bool = False) -> str:
    shop_info = f"{ma_shop}|{ten_shop}" if ten_shop else str(ma_shop)
    if is_hdd:
        return f"{shop_info} : đầu ghi không có playback"
    if is_dvr:
        return f"{shop_info} : đầu ghi mất kết nối"
    if is_no_data:
        return f"{shop_info} : {camera_text} cam không có playback"
    return f"{shop_info} : {camera_text} mất kết nối"


def build_description(camera_text: str, is_dvr: bool, is_no_data: bool = False, is_hdd: bool = False) -> str:
    if is_hdd:
        return "Dear A/c IT,  Đầu ghi shop không có playback, A/c hỗ trợ kiểm tra giúp em, em cảm ơn"
    if is_no_data:
        return f"Dear A/c IT, hiện tại {camera_text} không có dữ liệu A/c kiểm tra giúp em. Em cảm ơn!"
    if is_dvr:
        return "Dear A/c IT, hiện tại đầu ghi không vào được, hỗ trợ khắc phục giúp em, em cảm ơn."
    
    cam_str = str(camera_text)
    if not cam_str:
        cam_str = "camera"
        
    return f"Dear A/c IT, {cam_str} bị mất kết nối, nhờ a/c hỗ trợ kiểm tra và khắc phục giúp em. Em cảm ơn!"

