import pandas as pd
import requests
import json
import io

def test_motion():
    print("Creating dataset...")
    # Edge case 1: duplicate shops
    # Edge case 2: NaN in shop column
    # Edge case 3: numeric and non-numeric warning column
    # Let's test numeric first
    data_numeric = pd.DataFrame([
        {"Shop": "Shop A", "Warn": 5},
        {"Shop": "Shop B", "Warn": 10},
        {"Shop": "Shop A", "Warn": 2},
        {"Shop": pd.NA, "Warn": 3},
        {"Shop": "Shop C", "Warn": pd.NA}, # Should be treated carefully
    ])
    
    data_text = pd.DataFrame([
        {"Shop": "Shop A", "Warn": "Lỗi"},
        {"Shop": "Shop B", "Warn": "Lỗi"},
        {"Shop": "Shop A", "Warn": "Lỗi"},
        {"Shop": pd.NA, "Warn": "Lỗi"},
        {"Shop": "Shop C", "Warn": pd.NA},
    ])
    
    data_numeric.to_csv("test_numeric.csv", index=False)
    data_text.to_csv("test_text.csv", index=False)
    
    print("Testing numeric...")
    with open("test_numeric.csv", "rb") as f:
        res = requests.post("http://127.0.0.1:18020/api/motion/upload", files={"file": f})
    
    job_id = res.json()["data"]["job_id"]
    res2 = requests.post(f"http://127.0.0.1:18020/api/motion/jobs/{job_id}/analyze", data={"shop_col": "Shop", "warning_col": "Warn"})
    res3 = requests.get(f"http://127.0.0.1:18020/api/motion/jobs/{job_id}")
    
    results = res3.json()["data"]["results"]
    print("Numeric Results:")
    for r in results: print(r)
    
    # Shop B -> 10.0 -> 10
    # Shop A -> 7.0 -> 7
    # Shop C -> 0.0 -> 0 (since NA sum is 0 usually, wait: numeric coerce makes it NA, sum() makes it 0)
    
    print("Testing text...")
    with open("test_text.csv", "rb") as f:
        res = requests.post("http://127.0.0.1:18020/api/motion/upload", files={"file": f})
        
    job_id = res.json()["data"]["job_id"]
    res2 = requests.post(f"http://127.0.0.1:18020/api/motion/jobs/{job_id}/analyze", data={"shop_col": "Shop", "warning_col": "Warn"})
    res3 = requests.get(f"http://127.0.0.1:18020/api/motion/jobs/{job_id}")
    
    results = res3.json()["data"]["results"]
    print("Text Results:")
    for r in results: print(r)
    
test_motion()
