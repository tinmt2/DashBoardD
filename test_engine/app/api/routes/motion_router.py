import uuid
import tempfile
import os
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Dict, Any, List

from app.api.schemas.common import ApiResponse

router = APIRouter(prefix="/api/motion", tags=["motion"])

# Store uploaded files and their analysis state
MOTION_STORE: Dict[str, Dict[str, Any]] = {}

@router.post("/upload", response_model=ApiResponse)
async def upload_motion_file(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".csv" if file.filename.endswith(".csv") else ".xlsx")
    os.close(tmp_fd)
    
    with open(tmp_path, "wb") as buffer:
        buffer.write(await file.read())
        
    try:
        if tmp_path.endswith(".csv"):
            try: df = pd.read_csv(tmp_path, encoding='utf-8')
            except UnicodeDecodeError: df = pd.read_csv(tmp_path, encoding='utf-8-sig')
        else:
            df = pd.read_excel(tmp_path)
            
        columns = [str(c) for c in df.columns]
        
        MOTION_STORE[job_id] = {
            "status": "uploaded",
            "file_path": tmp_path,
            "columns": columns,
            "results": [],
            "error": None
        }
        
        return ApiResponse(success=True, status="ok", data={
            "job_id": job_id,
            "columns": columns
        })
        
    except Exception as e:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise HTTPException(status_code=400, detail=f"Không thể đọc file: {e}")

@router.post("/jobs/{job_id}/analyze", response_model=ApiResponse)
async def analyze_motion_data(
    job_id: str,
    shop_col: str = Form(...),
    warning_col: str = Form(...)
):
    if job_id not in MOTION_STORE:
        raise HTTPException(status_code=404, detail="Job không tồn tại")
        
    job_data = MOTION_STORE[job_id]
    tmp_path = job_data["file_path"]
    
    if not os.path.exists(tmp_path):
        job_data["status"] = "failed"
        job_data["error"] = "File đã bị xóa"
        raise HTTPException(status_code=400, detail="File đã bị xóa")
        
    try:
        if tmp_path.endswith(".csv"):
            try: df = pd.read_csv(tmp_path, encoding='utf-8')
            except UnicodeDecodeError: df = pd.read_csv(tmp_path, encoding='utf-8-sig')
        else:
            df = pd.read_excel(tmp_path)
            
        if shop_col not in df.columns or warning_col not in df.columns:
            raise ValueError(f"Cột {shop_col} hoặc {warning_col} không tồn tại trong dữ liệu")
            
        # Legacy Logic EXACT MATCH
        df_filtered = df.dropna(subset=[shop_col])
        is_numeric = pd.to_numeric(df_filtered[warning_col], errors='coerce').notna().any()
        
        if is_numeric:
            df_filtered[warning_col] = pd.to_numeric(df_filtered[warning_col], errors='coerce')
            result = df_filtered.groupby(shop_col)[warning_col].sum().reset_index()
        else:
            result = df_filtered.groupby(shop_col)[warning_col].count().reset_index()
            
        result = result.sort_values(by=warning_col, ascending=False)
        
        # Serialize to dict array
        results_list = []
        for _, row in result.iterrows():
            val = row[warning_col]
            if isinstance(val, float) and val.is_integer():
                val = int(val)
            results_list.append({
                "shop": str(row[shop_col]),
                "warning": val
            })
            
        job_data["status"] = "completed"
        job_data["results"] = results_list
        job_data["error"] = None
        
        return ApiResponse(success=True, status="ok", data={"job_id": job_id})
        
    except Exception as e:
        job_data["status"] = "failed"
        job_data["error"] = str(e)
        return ApiResponse(success=False, status="error", message=str(e))

@router.get("/jobs/{job_id}", response_model=ApiResponse)
async def get_motion_job(job_id: str):
    if job_id not in MOTION_STORE:
        raise HTTPException(status_code=404, detail="Job không tồn tại")
        
    data = MOTION_STORE[job_id].copy()
    data.pop("file_path", None) # Don't expose internal file path
    
    return ApiResponse(success=True, status="ok", data=data)
