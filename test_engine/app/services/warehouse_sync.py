import os
import re
import json
import requests
import datetime
import pandas as pd
from app.paths import RUNTIME_DIR
import logging

CACHE_FILE = RUNTIME_DIR / "warehouse_cache.json"
URL = "http://camera-giamsat-mon.fptshop.com.vn/warehouse-all"

def fetch_and_cache_warehouse():
    try:
        response = requests.get(URL, timeout=15)
        response.raise_for_status()
        
        match = re.search(r"var\s+listWarehouse\s*=\s*(\[.*?\]);", response.text, re.DOTALL)
        if not match:
            return False, "Không tìm thấy biến listWarehouse trong HTML"
            
        json_str = match.group(1)
        data = json.loads(json_str)
        
        if not data or not isinstance(data, list):
            return False, "Dữ liệu Warehouse không hợp lệ hoặc rỗng"
            
        cache_data = {
            "fetched_at": datetime.datetime.now().isoformat(),
            "source_url": URL,
            "record_count": len(data),
            "data": data
        }
        
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
        return True, "Thành công"
    except Exception as e:
        logging.error(f"Lỗi tải Warehouse: {e}")
        return False, str(e)

def get_warehouse_status():
    if not CACHE_FILE.exists():
        return {"status": "unavailable", "count": 0, "last_sync": None}
        
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)
            return {
                "status": "ready",
                "count": cache.get("record_count", 0),
                "last_sync": cache.get("fetched_at")
            }
    except Exception:
        return {"status": "error", "count": 0, "last_sync": None}

def get_warehouse_df():
    if not CACHE_FILE.exists():
        return pd.DataFrame()
        
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)
            data = cache.get("data", [])
            
        if not data:
            return pd.DataFrame()
            
        df = pd.DataFrame()
        df["STT"] = range(1, len(data) + 1)
        df["Brand"] = [str(d.get("brand", "")) for d in data]
        df["Shop Code"] = [str(d.get("warehouseId", "")) for d in data]
        df["Shop Name"] = [str(d.get("warehouseName", "")) for d in data]
        df["IP"] = [str(d.get("ip", "")) for d in data]
        
        return df
    except Exception:
        return pd.DataFrame()
