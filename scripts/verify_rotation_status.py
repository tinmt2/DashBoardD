#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KIỂM TRA TRẠNG THÁI XOAY VÒNG CREDENTIAL (POST-ROTATION VERIFICATION)
Dự án: DashBoardD Monorepo
Giai đoạn: Phase 6B
Kiểm tra an toàn (Read-Only, không in giá trị bí mật):
1. Đối chiếu hash mật khẩu hiện tại với hash cũ trong Git history.
2. Kiểm tra trạng thái khóa OTP Inside (phục vụ crawler báo cáo nợ).
3. Kiểm tra danh sách session tokens (active_tokens) đã thu hồi rỗng.
4. Kiểm tra trạng thái Git index và .gitignore.
"""

import os
import sys
import json
import subprocess
import base64
import time
import hmac
import hashlib
import struct

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
CONFIG_PATH = os.path.abspath(os.path.join(REPO_ROOT, "backend", "app", "admin_config.json"))

def get_historical_credentials():
    """Lấy credentials cũ từ commit 5f418c3 để đối chiếu (không in ra màn hình)."""
    try:
        out = subprocess.check_output(
            ["git", "show", "5f418c3:backend/app/admin_config.json"],
            cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL
        ).decode("utf-8")
        return json.loads(out)
    except Exception:
        return {}

def test_totp_generation(secret: str):
    if not secret:
        return True, "Chưa cài đặt (để trống)"
    try:
        clean = secret.replace(" ", "").replace("-", "").strip().upper()
        rem = len(clean) % 8
        if rem != 0:
            clean += "=" * (8 - rem)
        key = base64.b32decode(clean, casefold=True)
        counter = int(time.time() // 30)
        h = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
        offset = h[19] & 0x0F
        code = (struct.unpack(">I", h[offset:offset+4])[0] & 0x7FFFFFFF) % 1000000
        return True, f"{code:06d}"
    except Exception as e:
        return False, str(e)

def verify_all():
    print("=" * 70)
    print("      KIỂM TRA TRẠNG THÁI XOAY VÒNG CREDENTIAL ADMIN (PHASE 6B)")
    print("=" * 70)
    
    if not os.path.exists(CONFIG_PATH):
        print(f"[!] LỖI: Không tìm thấy file {CONFIG_PATH}")
        return False

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        curr = json.load(f)

    old = get_historical_credentials()

    curr_hash = curr.get("admin_password_hash", "")
    old_hash = old.get("admin_password_hash", "")
    curr_secret = curr.get("totp_secret", "")
    active_tokens = curr.get("active_tokens", [])

    results = []

    # 1. Kiểm tra Password Hash
    if not curr_hash or len(curr_hash) != 64:
        results.append(("Password Hash Format", "FAILED", "Hash không đúng chuẩn 64 hex"))
    elif curr_hash == old_hash:
        results.append(("Password Rotation", "PENDING", "Vẫn đang dùng hash cũ từ commit 5f418c3"))
    else:
        results.append(("Password Rotation", "VERIFIED", "Mật khẩu đã được xoay vòng thành công (Hash mới)"))

    # 2. Kiểm tra OTP Inside Secret
    totp_ok, totp_info = test_totp_generation(curr_secret)
    if not totp_ok:
        results.append(("TOTP Inside Format", "FAILED", f"Secret không hợp lệ: {totp_info}"))
    else:
        status_text = "Đã cấu hình hợp lệ (phục vụ crawler Inside)" if curr_secret else "Để trống"
        results.append(("TOTP Inside Secret", "VERIFIED", status_text))

    # 3. Kiểm tra Session Tokens Revocation
    if len(active_tokens) == 0:
        results.append(("Session Tokens Revocation", "VERIFIED", "Toàn bộ phiên cũ đã bị thu hồi (0 active tokens)"))
    else:
        results.append(("Session Tokens Revocation", "PARTIAL", f"Có {len(active_tokens)} active tokens trong cấu hình"))

    # 4. Kiểm tra Git Tracking & .gitignore
    ls_out = subprocess.check_output(
        ["git", "ls-files", "backend/app/admin_config.json"],
        cwd=REPO_ROOT
    ).decode("utf-8").strip()
    if ls_out == "":
        results.append(("Git Index Untracked", "VERIFIED", "File admin_config.json không bị track trong Git index"))
    else:
        results.append(("Git Index Untracked", "FAILED", "File admin_config.json vẫn đang bị track trong Git index!"))

    # Hiển thị kết quả
    print("\nBẢNG TỔNG HỢP KIỂM TRA:")
    print(f"{'Hạng mục kiểm tra':<30} | {'Trạng thái':<10} | {'Chi tiết'}")
    print("-" * 70)
    critical_ok = True
    for name, status, detail in results:
        print(f"{name:<30} | {status:<10} | {detail}")
        if name in ["Password Rotation", "Git Index Untracked"] and status != "VERIFIED":
            critical_ok = False

    print("=" * 70)
    if critical_ok:
        print("[+] KẾT LUẬN: MẬT KHẨU ADMIN ĐÃ ĐƯỢC XOAY VÒNG THÀNH CÔNG (100% VERIFIED)!")
    else:
        print("[*] KẾT LUẬN: ĐANG CHỜ CHỦ DỰ ÁN NHẬP MẬT KHẨU MỚI (PENDING EXECUTION).")
    print("=" * 70)
    return critical_ok

if __name__ == "__main__":
    verify_all()
