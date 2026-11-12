#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TOOL XOAY VÒNG CREDENTIAL ADMIN CỤC BỘ (CONTROLLED ADMIN CREDENTIAL ROTATION)
Dự án: DashBoardD Monorepo
Giai đoạn: Phase 6B
Tiêu chuẩn an toàn:
1. Nhập mật khẩu hiển thị dấu sao (*) để người dùng có phản hồi trực quan, không in mật khẩu ra log.
2. Làm rõ: Đăng nhập Admin CHỈ DÙNG MẬT KHẨU, không bắt buộc OTP điện thoại.
3. Khóa TOTP trong file cấu hình là OTP của hệ thống Inside / FPT Shop phục vụ crawler tự động:
   - Mặc định giữ nguyên khóa OTP Inside để không làm gián đoạn crawler báo cáo.
   - Hoặc cho phép cập nhật nếu người dùng có mã Inside mới.
4. Thu hồi toàn bộ session tokens cũ (active_tokens = []).
5. Tự động sao lưu file cấu hình trước khi ghi nguyên tử.
"""

import os
import sys
import json
import time
import shutil
import hashlib

# ==============================================================================
# 1. XÁC ĐỊNH ĐƯỜNG DẪN CẤU HÌNH (THÍCH ỨNG CHẠY TỪ ABC HOẶC DASHBOARDD)
# ==============================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

candidate_configs = [
    os.path.abspath(os.path.join(SCRIPT_DIR, "..", "backend", "app", "admin_config.json")),
    os.path.abspath(os.path.join(SCRIPT_DIR, "..", "DashBoardD", "backend", "app", "admin_config.json")),
    os.path.abspath(os.path.join(os.getcwd(), "backend", "app", "admin_config.json")),
    os.path.abspath(os.path.join(os.getcwd(), "DashBoardD", "backend", "app", "admin_config.json")),
    r"D:\Tín\ABC\DashBoardD\backend\app\admin_config.json"
]

CONFIG_PATH = None
for p in candidate_configs:
    if os.path.exists(p):
        CONFIG_PATH = p
        break

if not CONFIG_PATH:
    CONFIG_PATH = candidate_configs[0]

BACKUP_DIR = r"D:\Tín\ABC\_backups_phase6b"

# ==============================================================================
# 2. CÁC HÀM TIỆN ÍCH AN TOÀN
# ==============================================================================
def hash_password(password: str) -> str:
    """Tương thích 100% với backend/app/api/admin.py _hash_pw()"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def secure_input_password(prompt: str = ">> Nhập mật khẩu: ") -> str:
    """
    Nhập mật khẩu hiển thị dấu sao (*) trên console để người dùng biết đã nhận phím.
    Hỗ trợ xóa lùi bằng Backspace và kết thúc bằng Enter.
    """
    try:
        import msvcrt
        sys.stdout.write(prompt)
        sys.stdout.flush()
        pw_chars = []
        while True:
            ch = msvcrt.getwch()
            if ch in ('\r', '\n'):
                sys.stdout.write('\n')
                sys.stdout.flush()
                break
            elif ch == '\x03':  # Ctrl+C
                sys.stdout.write('\n')
                sys.stdout.flush()
                raise KeyboardInterrupt
            elif ch == '\x08':  # Backspace
                if len(pw_chars) > 0:
                    pw_chars.pop()
                    sys.stdout.write('\b \b')
                    sys.stdout.flush()
            elif ch in ('\x00', '\xe0'):  # Phím điều hướng / Function key
                msvcrt.getwch()
            else:
                pw_chars.append(ch)
                sys.stdout.write('*')
                sys.stdout.flush()
        return "".join(pw_chars)
    except Exception:
        import getpass
        return getpass.getpass(prompt)

# ==============================================================================
# 3. QUY TRÌNH XOAY VÒNG CỤC BỘ
# ==============================================================================
def run_rotation():
    print("=" * 70)
    print("    CÔNG CỤ XOAY VÒNG MẬT KHẨU ADMIN - DASHBOARDD (PHASE 6B)")
    print("=" * 70)
    print(f"[*] Đường dẫn file cấu hình: {CONFIG_PATH}")
    
    if not os.path.exists(CONFIG_PATH):
        print(f"[!] LỖI: Không tìm thấy file {CONFIG_PATH}")
        sys.exit(1)

    # 1. Đọc file hiện tại
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            current_cfg = json.load(f)
    except Exception as e:
        print(f"[!] LỖI khi đọc file cấu hình: {e}")
        sys.exit(1)

    current_username = current_cfg.get("admin_username", "admin")
    current_totp = current_cfg.get("totp_secret", "")
    print(f"[*] Tài khoản quản trị: '{current_username}'")
    print(f"[*] Trạng thái OTP Inside: {'Đã có khóa cấu hình' if current_totp else 'Chưa cấu hình'}")
    print("-" * 70)
    print("[*] LƯU Ý QUAN TRỌNG:")
    print("    - Đăng nhập Admin CHỈ CẦN MẬT KHẨU (không bắt buộc OTP trên điện thoại).")
    print("    - Khóa TOTP trong hệ thống là mã OTP của Inside/FPT phục vụ crawler tự động.")
    print("-" * 70)

    # 2. Nhập mật khẩu mới an toàn với dấu sao (*)
    while True:
        pw1 = secure_input_password(">> Nhập MẬT KHẨU ADMIN MỚI (tối thiểu 8 ký tự): ")
        if len(pw1) < 8:
            print("[!] Cảnh báo: Mật khẩu quá ngắn, vui lòng chọn mật khẩu từ 8 ký tự trở lên!\n")
            continue
        pw2 = secure_input_password(">> Nhập lại mật khẩu mới để xác nhận: ")
        if pw1 != pw2:
            print("[!] Lỗi: Hai lần nhập mật khẩu không khớp nhau. Vui lòng nhập lại!\n")
            continue
        break

    new_hash = hash_password(pw1)
    del pw1
    del pw2

    # 3. Xử lý khóa TOTP Inside
    print("\n" + "-" * 70)
    print("CẤU HÌNH KHÓA OTP INSIDE / FPT (CRAWLER BÁO CÁO NỢ):")
    print(" [1] Giữ nguyên khóa OTP Inside hiện tại (Khuyến nghị để crawler FPT chạy bình thường)")
    print(" [2] Nhập khóa Secret Inside mới (nếu bạn có mã Base32 mới từ Authenticator)")
    print(" [3] Xóa bỏ / để trống khóa OTP Inside")
    print("-" * 70)

    choice = input(">> Nhập lựa chọn của bạn [1-3, mặc định 1]: ").strip()
    if not choice:
        choice = "1"

    final_totp = current_totp
    if choice == "2":
        new_totp_input = input(">> Nhập chuỗi Secret Base32 của Inside: ").strip().replace(" ", "").upper()
        if new_totp_input:
            final_totp = new_totp_input
            print("[+] Đã nhận khóa Secret Inside mới.")
        else:
            print("[*] Không có chuỗi mới, giữ nguyên khóa cũ.")
    elif choice == "3":
        final_totp = ""
        print("[+] Đã xóa bỏ khóa OTP Inside.")
    else:
        print("[+] Giữ nguyên khóa OTP Inside hiện tại.")

    # 4. Tạo bản sao lưu an toàn trước khi ghi
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"admin_config.json.bak.{timestamp}")
    try:
        shutil.copy2(CONFIG_PATH, backup_file)
        print(f"\n[+] Đã tạo bản sao lưu an toàn tại: {backup_file}")
    except Exception as e:
        print(f"[!] LỖI: Không thể tạo bản sao lưu: {e}. Hủy quy trình ghi.")
        sys.exit(1)

    # 5. Ghi nguyên tử (Atomic write via temporary file)
    new_cfg = {
        "admin_username": current_username,
        "admin_password_hash": new_hash,
        "active_tokens": [],  # Thu hồi toàn bộ session tokens cũ
        "totp_secret": final_totp
    }

    tmp_path = CONFIG_PATH + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(new_cfg, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, CONFIG_PATH)
        print("[+] Đã cập nhật nguyên tử file admin_config.json thành công!")
    except Exception as e:
        print(f"[!] LỖI trong quá trình ghi file: {e}")
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, CONFIG_PATH)
            print("[*] Đã tự động khôi phục lại file gốc từ bản sao lưu.")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("             HOÀN TẤT XOAY VÒNG CREDENTIAL ADMIN THÀNH CÔNG!")
    print("=" * 70)
    print("[1] Mật khẩu Admin mới: ĐÃ ĐƯỢC THIẾT LẬP (Hash SHA-256 an toàn).")
    print(f"[2] Khóa OTP Inside   : {'Đã giữ nguyên/cập nhật' if final_totp else 'Đã xóa bỏ'}.")
    print("[3] Session Tokens cũ : ĐÃ BỊ THU HỒI HOÀN TOÀN (active_tokens = []).")
    print(f"[4] Bản sao lưu       : {backup_file}")
    print("-" * 70)
    print("(*) Lưu ý: Mật khẩu cũ trong lịch sử Git GitHub hiện đã trở thành CHUỖI VÔ GIÁ TRỊ (DEAD SECRET).")
    print("=" * 70)

if __name__ == "__main__":
    if "--check-only" in sys.argv:
        print("ROTATE_SCRIPT_CHECK: Syntax and imports OK.")
        sys.exit(0)
    run_rotation()
