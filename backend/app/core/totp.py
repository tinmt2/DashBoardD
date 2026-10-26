import hmac
import base64
import struct
import hashlib
import time
import os
import json
import logging
import urllib.parse
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "admin_config.json")

def _parse_protobuf_varint(buffer: bytes, pos: int):
    res = 0
    shift = 0
    while pos < len(buffer):
        b = buffer[pos]
        pos += 1
        res |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return res, pos

def parse_migration_uri(migration_uri: str) -> List[Dict[str, str]]:
    """
    Giải mã URL xuất tài khoản từ Google Authenticator:
    otpauth-migration://offline?data=Ci0K...
    """
    try:
        parsed = urllib.parse.urlparse(migration_uri.strip())
        qs = urllib.parse.parse_qs(parsed.query)
        data_param = qs.get("data", [""])[0]
        if not data_param:
            return []

        # Giải mã base64 (cho phép thiếu padding)
        b64_str = urllib.parse.unquote(data_param).strip()
        rem = len(b64_str) % 4
        if rem > 0:
            b64_str += "=" * (4 - rem)
        raw = base64.b64decode(b64_str)

        accounts = []
        pos = 0
        while pos < len(raw):
            key, pos = _parse_protobuf_varint(raw, pos)
            field_num = key >> 3
            wire_type = key & 0x7
            if wire_type == 2:  # length-delimited
                length, pos = _parse_protobuf_varint(raw, pos)
                chunk = raw[pos : pos + length]
                pos += length

                if field_num == 1:
                    # OtpParameters
                    sub_pos = 0
                    sec_bytes = None
                    name = ""
                    issuer = ""
                    while sub_pos < len(chunk):
                        skey, sub_pos = _parse_protobuf_varint(chunk, sub_pos)
                        sfield = skey >> 3
                        swire = skey & 0x7
                        if swire == 2:
                            slen, sub_pos = _parse_protobuf_varint(chunk, sub_pos)
                            sval = chunk[sub_pos : sub_pos + slen]
                            sub_pos += slen
                            if sfield == 1:
                                sec_bytes = sval
                            elif sfield == 2:
                                name = sval.decode("utf-8", errors="ignore")
                            elif sfield == 3:
                                issuer = sval.decode("utf-8", errors="ignore")
                        elif swire == 0:
                            _, sub_pos = _parse_protobuf_varint(chunk, sub_pos)
                        elif swire == 1:
                            sub_pos += 8
                        elif swire == 5:
                            sub_pos += 4
                        else:
                            break

                    if sec_bytes:
                        base32_sec = (
                            base64.b32encode(sec_bytes)
                            .decode("ascii")
                            .replace("=", "")
                        )
                        accounts.append(
                            {
                                "secret": base32_sec,
                                "name": name,
                                "issuer": issuer,
                            }
                        )
            elif wire_type == 0:
                _, pos = _parse_protobuf_varint(raw, pos)
            elif wire_type == 1:
                pos += 8
            elif wire_type == 5:
                pos += 4
            else:
                break
        return accounts
    except Exception as e:
        logger.error(f"[TOTP] Lỗi giải mã otpauth-migration: {e}")
        return []

def extract_secret_from_input(raw_input: str) -> Optional[str]:
    """
    Tự động nhận diện và trích xuất chuỗi Secret Key từ nhiều định dạng khác nhau:
    1. otpauth-migration://offline?data=... (Xuất từ Google Authenticator)
    2. otpauth://totp/...?secret=... (Quét từ mã QR thông thường)
    3. Chuỗi Base32 trực tiếp (VD: JBSWY3DPEHPK3PXP...)
    """
    if not raw_input:
        return None

    cleaned = raw_input.strip()

    # 1. Format: otpauth-migration
    if "otpauth-migration" in cleaned.lower() or "offline?data=" in cleaned.lower():
        accounts = parse_migration_uri(cleaned)
        if accounts:
            # Ưu tiên lấy tài khoản có liên quan tới FPT/FRT nếu có, hoặc lấy tài khoản đầu tiên
            for acc in accounts:
                name_issuer = (acc.get("name", "") + " " + acc.get("issuer", "")).lower()
                if any(k in name_issuer for k in ["fpt", "frt", "retail", "longchau", "vaccine"]):
                    return acc["secret"]
            return accounts[0]["secret"]
        return None

    # 2. Format: otpauth://
    if "otpauth://" in cleaned.lower():
        try:
            parsed = urllib.parse.urlparse(cleaned)
            qs = urllib.parse.parse_qs(parsed.query)
            secret_param = qs.get("secret", [""])[0]
            if secret_param:
                cleaned = secret_param
        except Exception:
            pass

    # 3. Chuỗi Base32 chuẩn hóa
    secret = cleaned.replace(" ", "").replace("-", "").strip().upper()
    # Kiểm tra xem có sinh được OTP hợp lệ không
    if generate_totp(secret):
        return secret
    return None

def generate_totp(secret: str) -> Optional[str]:
    """
    Sinh mã TOTP 6 chữ số từ secret key (RFC 6238).
    """
    if not secret:
        return None
    try:
        clean_secret = secret.replace(" ", "").replace("-", "").strip().upper()
        missing_padding = len(clean_secret) % 8
        if missing_padding != 0:
            clean_secret += "=" * (8 - missing_padding)

        key = base64.b32decode(clean_secret, casefold=True)
        counter = int(time.time() // 30)
        counter_bytes = struct.pack(">Q", counter)

        hmac_digest = hmac.new(key, counter_bytes, hashlib.sha1).digest()
        offset = hmac_digest[19] & 0x0F
        code_int = (
            struct.unpack(">I", hmac_digest[offset : offset + 4])[0] & 0x7FFFFFFF
        ) % 1000000

        return f"{code_int:06d}"
    except Exception as e:
        logger.debug(f"[TOTP] Error generating TOTP: {e}")
        return None

def get_admin_totp_secret() -> str:
    """Đọc secret key cấu hình trong admin_config.json"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                return (cfg.get("totp_secret") or "").strip()
        except Exception:
            pass
    return ""

def get_current_totp_code() -> Optional[str]:
    """Lấy mã OTP 6 số hiện tại nếu đã cài Secret Key"""
    secret = get_admin_totp_secret()
    if secret:
        return generate_totp(secret)
    return None
