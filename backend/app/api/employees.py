import urllib.parse
from typing import List, Optional
from datetime import datetime, timezone, date
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.employee import Employee, EmployeeTransferHistory, MonthlyScheduleLink, EmployeeShift
from app.services.sharepoint.browser_session import SharePointBrowserSession, DEFAULT_SHAREPOINT_URL

router = APIRouter()

DEFAULT_EMPLOYEES = [
    {"inside_code": "51765", "id": "VienND2", "name": "Ngô Đức Viện", "chain": "FPT Shop", "status": "Active"},
    {"inside_code": "51771", "id": "DatNT215", "name": "Nguyễn Tấn Đạt", "chain": "FPT Shop", "status": "Active"},
    {"inside_code": "34139", "id": "TinMT2", "name": "Mai Trọng Tín", "chain": "FPT Shop", "status": "Active"},
    {"inside_code": "51799", "id": "HieuPM26", "name": "Phạm Minh Hiếu", "chain": "FPT Shop", "status": "Active"},
    {"inside_code": "51794", "id": "TuanPA48", "name": "Phùng Anh Tuấn", "chain": "FPT Shop", "status": "Active"},
    {"inside_code": "32690", "id": "LuanNV8", "name": "Nguyễn Văn Luân", "chain": "Long Châu", "status": "Active"},
    {"inside_code": "51779", "id": "MinhPP2", "name": "Phạm Phú Minh", "chain": "Vaccine", "status": "Active"},
    {"inside_code": "51784", "id": "QuyNN13", "name": "Nguyễn Ngọc Quý", "chain": "Vaccine", "status": "Active"},
    {"inside_code": "51786", "id": "TanTQ6", "name": "Trần Quang Tân", "chain": "Long Châu", "status": "Active"},
    {"inside_code": "51792", "id": "TuongPN3", "name": "Phan Ngọc Tường", "chain": "Vaccine", "status": "Active"},
    {"inside_code": "51793", "id": "BaoTDC", "name": "Trần Đức Chí Bảo", "chain": "Long Châu", "status": "Active"},
    {"inside_code": "51795", "id": "SonDQ3", "name": "Đặng Quang Sơn", "chain": "Long Châu", "status": "Active"},
    {"inside_code": "51796", "id": "DucNM79", "name": "Nguyễn Minh Đức", "chain": "Long Châu", "status": "Active"},
    {"inside_code": "12678", "id": "ViDNT2", "name": "Đỗ Ngọc Thúy Vi", "chain": "FPT Shop", "status": "Active"},
    {"inside_code": "42372", "id": "DuyenNTM20", "name": "Nguyễn Thị Mỹ Duyên", "chain": "FPT Shop", "status": "Active"},
    {"inside_code": "51800", "id": "SangLM4", "name": "Lê Minh Sáng", "chain": "FPT Shop", "status": "Active"},
    {"inside_code": "51801", "id": "TamNT54", "name": "Nguyễn Thanh Tâm", "chain": "Long Châu", "status": "Active"},
    {"inside_code": "51803", "id": "SonTCH", "name": "Trần Công Hoàng Sơn", "chain": "Long Châu", "status": "Active"},
    {"inside_code": "100859", "id": "ThanhNN25", "name": "Nguyễn Ngọc Thanh", "chain": "Vaccine", "status": "Active"},
    {"inside_code": "111358", "id": "QuyNV34", "name": "Nguyễn Văn Quý", "chain": "Long Châu", "status": "Active"},
    {"inside_code": "51806", "id": "TaiVM3", "name": "Võ Minh Tài", "chain": "Vaccine", "status": "Active"},
    {"inside_code": "51808", "id": "ThongHQ3", "name": "Hồ Quốc Thông", "chain": "Long Châu", "status": "Active"},
    {"inside_code": "51809", "id": "DatCT10", "name": "Chiêng Tấn Đạt", "chain": "Long Châu", "status": "Active"},
    {"inside_code": "51810", "id": "PhongTTH2", "name": "Trần Trương Huy Phong", "chain": "Vaccine", "status": "Active"},
    {"inside_code": "107683", "id": "HienPN3", "name": "Phạm Ngọc Hiền", "chain": "Long Châu", "status": "Active"},
    {"inside_code": "55003", "id": "DuongNP", "name": "Nguyễn Phi Dương", "chain": "Vaccine", "status": "Active"},
    {"inside_code": "55005", "id": "LinhLT47", "name": "Lý Thành Linh", "chain": "Long Châu", "status": "Active"},
    {"inside_code": "55006", "id": "DuanHX", "name": "Hoàng Xuân Duẩn", "chain": "Long Châu", "status": "Active"},
    {"inside_code": "62997", "id": "NhanDT27", "name": "Dương Thành Nhân", "chain": "Vaccine", "status": "Active"},
    {"inside_code": "109476", "id": "TuNM35", "name": "Nguyễn Minh Tú", "chain": "Long Châu", "status": "Active"},
    {"inside_code": "110494", "id": "TamNM25", "name": "Nguyễn Minh Tâm", "chain": "FPT Shop", "status": "Active"},
    {"inside_code": "110510", "id": "VyTTH6", "name": "Tạ Trần Hà Vy", "chain": "Long Châu", "status": "Active"},
    {"inside_code": "66651", "id": "MyPTK4", "name": "Phạm Thị Kiều My", "chain": "FPT Shop", "status": "Active"},
    {"inside_code": "68855", "id": "NgocTB35", "name": "Trác Bảo Ngọc", "chain": "Long Châu", "status": "Active"},
    {"inside_code": "69846", "id": "TamLM10", "name": "Lê Minh Tâm", "chain": "FPT Shop", "status": "Active"},
    {"inside_code": "112060", "id": "SonTT37", "name": "Trần Thiện Sơn", "chain": "Long Châu", "status": "Active"},
    {"inside_code": "72033", "id": "AnHSH2", "name": "Hứa Sang Hoàng Ân", "chain": "FPT Shop", "status": "Active"},
    {"inside_code": "112661", "id": "DinhLV8", "name": "Lý Văn Định", "chain": "FPT Shop", "status": "Active"},
]

def _seed_if_empty(db: Session):
    count = db.query(Employee).count()
    if count == 0:
        for item in DEFAULT_EMPLOYEES:
            emp = Employee(
                id=item["id"],
                inside_code=item.get("inside_code", ""),
                name=item["name"],
                chain=item["chain"],
                status=item["status"],
                total_errors=0,
                total_checked=0
            )
            db.add(emp)
        db.commit()

def serialize_employee(e: Employee) -> dict:
    return {
        "id": e.id,
        "insideCode": e.inside_code or "",
        "name": e.name,
        "chain": e.chain,
        "position": e.position or "",
        "status": e.status,
        "startDate": e.start_date or "",
        "totalErrors": e.total_errors or 0,
        "totalChecked": e.total_checked or 0,
        "lastActivity": e.last_activity or "",
        "createdAt": e.created_at.isoformat() if e.created_at else "",
        "updatedAt": e.updated_at.isoformat() if e.updated_at else "",
    }

def serialize_history(h: EmployeeTransferHistory) -> dict:
    return {
        "employeeId": h.employee_id,
        "fromChain": h.from_chain,
        "toChain": h.to_chain,
        "transferredAt": h.transferred_at.isoformat() if h.transferred_at else "",
        "transferredBy": h.transferred_by or "Admin",
    }

class EmployeeCreateRequest(BaseModel):
    id: str
    insideCode: Optional[str] = ""
    name: str
    chain: str
    position: Optional[str] = ""
    status: Optional[str] = "Active"
    startDate: Optional[str] = ""

class EmployeeUpdateRequest(BaseModel):
    insideCode: Optional[str] = None
    name: Optional[str] = None
    chain: Optional[str] = None
    position: Optional[str] = None
    status: Optional[str] = None
    startDate: Optional[str] = None

class MoveEmployeeRequest(BaseModel):
    targetChain: str
    transferredBy: Optional[str] = "Admin"

@router.get("")
def get_employees(chain: Optional[str] = Query(None), db: Session = Depends(get_db)):
    _seed_if_empty(db)
    query = db.query(Employee)
    if chain:
        query = query.filter(Employee.chain == chain)
    employees = query.all()
    return [serialize_employee(e) for e in employees]

@router.post("")
def create_employee(req: EmployeeCreateRequest, db: Session = Depends(get_db)):
    existing = db.query(Employee).filter(Employee.id == req.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Mã nhân viên đã tồn tại trên hệ thống!")
    
    emp = Employee(
        id=req.id.strip(),
        inside_code=(req.insideCode or "").strip(),
        name=req.name.strip(),
        chain=req.chain,
        position=req.position,
        status=req.status or "Active",
        start_date=req.startDate,
        total_errors=0,
        total_checked=0
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return serialize_employee(emp)

@router.put("/{emp_id}")
def update_employee(emp_id: str, req: EmployeeUpdateRequest, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên!")
    
    if req.insideCode is not None:
        emp.inside_code = req.insideCode.strip()
    if req.name is not None:
        emp.name = req.name.strip()
    if req.chain is not None:
        emp.chain = req.chain
    if req.position is not None:
        emp.position = req.position
    if req.status is not None:
        emp.status = req.status
    if req.startDate is not None:
        emp.start_date = req.startDate
    
    emp.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(emp)
    return serialize_employee(emp)

@router.post("/{emp_id}/move")
def move_employee(emp_id: str, req: MoveEmployeeRequest, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên!")
    
    if emp.chain == req.targetChain:
        raise HTTPException(status_code=400, detail="Nhân viên đã ở chuỗi này!")
    
    old_chain = emp.chain
    emp.chain = req.targetChain
    emp.updated_at = datetime.now(timezone.utc)
    
    history = EmployeeTransferHistory(
        employee_id=emp_id,
        from_chain=old_chain,
        to_chain=req.targetChain,
        transferred_by=req.transferredBy or "Admin"
    )
    db.add(history)
    db.commit()
    db.refresh(emp)
    return serialize_employee(emp)

@router.delete("/{emp_id}")
def delete_employee(emp_id: str, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên!")
    
    db.delete(emp)
    db.commit()
    return {"success": True, "message": "Đã xóa nhân viên thành công!"}

@router.get("/{emp_id}/history")
def get_employee_history(emp_id: str, db: Session = Depends(get_db)):
    records = db.query(EmployeeTransferHistory).filter(
        EmployeeTransferHistory.employee_id == emp_id
    ).order_by(EmployeeTransferHistory.transferred_at.desc()).all()
    return [serialize_history(h) for h in records]

# ─── SharePoint Browser Session & Monthly Schedule Endpoints ────────────────

def _extract_filename_from_url(url: str) -> str:
    try:
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        if "file" in params and params["file"]:
            return urllib.parse.unquote(params["file"][0])
        path_parts = parsed.path.split("/")
        if path_parts and path_parts[-1].endswith(".xlsx"):
            return urllib.parse.unquote(path_parts[-1])
    except Exception:
        pass
    return "1. LLV.xlsx"

def _seed_schedule_links_if_empty(db: Session):
    count = db.query(MonthlyScheduleLink).count()
    if count == 0:
        default_link = MonthlyScheduleLink(
            month="2026-11",
            title="Lịch làm việc Tháng 11/2026",
            file_name="1. LLV T11 2026.xlsx",
            sharepoint_url=DEFAULT_SHAREPOINT_URL,
            note="Bảng phân ca làm việc FPT Shop, Long Châu, Vaccine"
        )
        db.add(default_link)
        db.commit()

def serialize_schedule_link(link: MonthlyScheduleLink) -> dict:
    return {
        "id": link.id,
        "month": link.month,
        "title": link.title or f"Lịch làm việc Tháng {link.month}",
        "fileName": link.file_name or "1. LLV.xlsx",
        "sharepointUrl": link.sharepoint_url,
        "note": link.note or "",
        "createdAt": link.created_at.isoformat() if link.created_at else "",
        "updatedAt": link.updated_at.isoformat() if link.updated_at else "",
    }

class ScheduleLinkUpsertRequest(BaseModel):
    month: str
    sharepointUrl: str
    title: Optional[str] = None
    fileName: Optional[str] = None
    note: Optional[str] = None

class SharePointAuthStartRequest(BaseModel):
    targetUrl: Optional[str] = None

class SharePointOpenUrlRequest(BaseModel):
    url: str

@router.get("/sharepoint/auth/status")
def get_sharepoint_auth_status():
    session = SharePointBrowserSession.get_instance()
    status = session.get_status()
    has_cookies = session.has_stored_cookies()
    return {
        "authenticated": status == "AUTHENTICATED",
        "status": status,
        "hasCookies": has_cookies,
        "profileName": session.profile_name
    }

@router.post("/sharepoint/auth/start")
def start_sharepoint_auth(req: SharePointAuthStartRequest = None):
    session = SharePointBrowserSession.get_instance()
    url = req.targetUrl if req and req.targetUrl else None
    status = session.start_login(url)
    return {
        "authenticated": status == "AUTHENTICATED",
        "status": status,
        "hasCookies": session.has_stored_cookies()
    }

@router.post("/sharepoint/auth/open")
def open_sharepoint_url(req: SharePointOpenUrlRequest):
    session = SharePointBrowserSession.get_instance()
    ok = session.open_schedule_url(req.url)
    return {"success": ok}

@router.post("/sharepoint/auth/stop")
def stop_sharepoint_auth():
    session = SharePointBrowserSession.get_instance()
    if session.driver:
        try:
            session.driver.quit()
        except Exception:
            pass
        session.clear_driver()
    session.status = "STOPPED"
    return {"success": True, "status": "STOPPED"}

@router.post("/sharepoint/auth/logout")
def logout_sharepoint_auth():
    session = SharePointBrowserSession.get_instance()
    session.logout()
    return {"success": True, "status": "STOPPED", "authenticated": False}

@router.get("/schedule-links")
def get_schedule_links(month: Optional[str] = Query(None), db: Session = Depends(get_db)):
    _seed_schedule_links_if_empty(db)
    if month:
        link = db.query(MonthlyScheduleLink).filter(MonthlyScheduleLink.month == month).first()
        return serialize_schedule_link(link) if link else None
    links = db.query(MonthlyScheduleLink).order_by(MonthlyScheduleLink.month.desc()).all()
    return [serialize_schedule_link(l) for l in links]

@router.post("/schedule-links")
def upsert_schedule_link(req: ScheduleLinkUpsertRequest, db: Session = Depends(get_db)):
    clean_month = req.month.strip()
    clean_url = req.sharepointUrl.strip()
    if not clean_month or not clean_url:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp đầy đủ Tháng (YYYY-MM) và Link SharePoint!")
    
    file_name = req.fileName or _extract_filename_from_url(clean_url)
    title = req.title
    if not title:
        parts = clean_month.split("-")
        title = f"Lịch làm việc Tháng {parts[1]}/{parts[0]}" if len(parts) == 2 else f"Lịch làm việc Tháng {clean_month}"
        
    existing = db.query(MonthlyScheduleLink).filter(MonthlyScheduleLink.month == clean_month).first()
    if existing:
        existing.sharepoint_url = clean_url
        existing.file_name = file_name
        existing.title = title
        if req.note is not None:
            existing.note = req.note
        existing.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return serialize_schedule_link(existing)
    else:
        new_link = MonthlyScheduleLink(
            month=clean_month,
            title=title,
            file_name=file_name,
            sharepoint_url=clean_url,
            note=req.note or ""
        )
        db.add(new_link)
        db.commit()
        db.refresh(new_link)
        return serialize_schedule_link(new_link)

@router.delete("/schedule-links/{month}")
def delete_schedule_link(month: str, db: Session = Depends(get_db)):
    link = db.query(MonthlyScheduleLink).filter(MonthlyScheduleLink.month == month).first()
    if not link:
        raise HTTPException(status_code=404, detail="Không tìm thấy liên kết tháng này!")
    db.delete(link)
    db.commit()
    return {"success": True, "message": f"Đã xóa liên kết {month}"}

@router.post("/schedule/import-excel")
async def import_schedule_excel(
    file: UploadFile = File(...),
    month: str = Form("2026-11"),
    db: Session = Depends(get_db)
):
    try:
        import io
        import openpyxl
        contents = await file.read()
        wb = openpyxl.load_workbook(filename=io.BytesIO(contents), data_only=True)
        
        sheet = None
        for sname in wb.sheetnames:
            if "LLV" in sname.upper() or month in sname:
                sheet = wb[sname]
                break
        if not sheet:
            sheet = wb.active
            
        date_cols = {}
        mail_col_idx = None
        code_col_idx = None
        name_col_idx = None
        header_row_idx = 2
        
        for r in range(1, 6):
            for c in range(1, sheet.max_column + 1):
                val = sheet.cell(row=r, column=c).value
                if val is not None:
                    val_str = str(val).strip().lower()
                    if val_str == "mail" and mail_col_idx is None:
                        mail_col_idx = c
                        header_row_idx = r
                    elif val_str in ("mã", "ma", "mã nv", "id") and code_col_idx is None:
                        code_col_idx = c
                    elif val_str in ("tên", "họ và tên", "họ tên", "name") and name_col_idx is None:
                        name_col_idx = c
                        
        if not mail_col_idx:
            mail_col_idx = 7
            code_col_idx = 6
            name_col_idx = 8
            header_row_idx = 2

        for c in range(1, sheet.max_column + 1):
            val = sheet.cell(row=header_row_idx, column=c).value
            dow_val = sheet.cell(row=max(1, header_row_idx - 1), column=c).value
            dow_str = str(dow_val).strip() if dow_val else ""
            
            d_str = None
            if isinstance(val, (datetime, date)):
                d_str = val.strftime("%Y-%m-%d")
            elif val is not None:
                vs = str(val).strip()
                for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d"):
                    try:
                        parsed_d = datetime.strptime(vs, fmt)
                        d_str = parsed_d.strftime("%Y-%m-%d")
                        break
                    except ValueError:
                        pass
            if d_str:
                date_cols[c] = {"date_str": d_str, "day_of_week": dow_str}

        db.query(EmployeeShift).filter(EmployeeShift.month == month).delete()
        
        emp_records = db.query(Employee).all()
        emp_chain_map = {e.id.lower(): e.chain for e in emp_records}
        emp_name_map = {e.id.lower(): e.name for e in emp_records}

        imported_count = 0
        added_employees = set()
        
        for r in range(header_row_idx + 1, sheet.max_row + 1):
            mail_val = sheet.cell(row=r, column=mail_col_idx).value
            if not mail_val:
                continue
            emp_mail = str(mail_val).strip()
            if not emp_mail or len(emp_mail) < 3 or "tổng" in emp_mail.lower():
                continue
                
            code_val = sheet.cell(row=r, column=code_col_idx).value if code_col_idx else ""
            emp_code = str(code_val).strip() if code_val else ""
            
            name_val = sheet.cell(row=r, column=name_col_idx).value if name_col_idx else ""
            emp_name = str(name_val).strip() if name_val else emp_name_map.get(emp_mail.lower(), emp_mail)
            
            chain = emp_chain_map.get(emp_mail.lower(), "FPT Shop")
            added_employees.add(emp_mail)
            
            for c, dinfo in date_cols.items():
                shift_val = sheet.cell(row=r, column=c).value
                if shift_val:
                    stype = str(shift_val).strip()
                    if stype:
                        shift_obj = EmployeeShift(
                            month=month,
                            employee_id=emp_mail,
                            employee_code=emp_code,
                            employee_name=emp_name,
                            chain=chain,
                            date=dinfo["date_str"],
                            shift_type=stype,
                            day_of_week=dinfo["day_of_week"]
                        )
                        db.add(shift_obj)
                        imported_count += 1
                        
        db.commit()
        return {
            "success": True,
            "month": month,
            "importedCount": imported_count,
            "employeesCount": len(added_employees),
            "daysCount": len(date_cols)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý file Excel ca trực: {str(e)}")

def _seed_demo_shifts_if_empty(db: Session, target_month: str = "2026-11"):
    import calendar
    from datetime import date
    dow_names = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
    
    parts = target_month.split("-")
    year = int(parts[0])
    month_num = int(parts[1])
    days_in_month = calendar.monthrange(year, month_num)[1]
    
    month_dates = []
    for day in range(1, days_in_month + 1):
        d = date(year, month_num, day)
        month_dates.append((d.strftime("%Y-%m-%d"), dow_names[d.weekday()]))

    sample_rows = [
        {"code": "50407", "id": "AnNT50", "name": "Nguyễn Tấn An", "chain": "FPT Shop", "pattern": ["Ca Sáng", "Ca Sáng", "Ca Sáng", "Ca Sáng", "Ca Sáng", "Trực đêm", "OFF"]},
        {"code": "51765", "id": "VienND2", "name": "Ngô Đức Viện", "chain": "FPT Shop", "pattern": ["Ca Sáng", "Ca Chiều", "Ca Sáng", "Ca Sáng", "OFF", "Ca Sáng", "OFF"]},
        {"code": "51771", "id": "DatNT215", "name": "Nguyễn Tấn Đạt", "chain": "FPT Shop", "pattern": ["Trực đêm", "OFF", "Ca Chiều", "Ca Sáng", "Ca Chiều", "Ca Sáng", "Sáng + đêm"]},
        {"code": "34139", "id": "TinMT2", "name": "Mai Trọng Tín", "chain": "FPT Shop", "pattern": ["OFF", "OFF BÙ", "OFF PHÉP", "Ca Chiều", "Trực đêm", "OFF", "Ca Sáng", "OFF", "OFF BÙ", "Trực đêm", "OFF", "Ca Sáng", "Ca Sáng", "Ca Sáng", "OFF"]},
        {"code": "51799", "id": "HieuPM26", "name": "Phạm Minh Hiếu", "chain": "FPT Shop", "pattern": ["Ca Sáng", "Trực đêm", "OFF", "Ca Chiều", "Ca Sáng", "Ca Sáng", "OFF"]},
        {"code": "51794", "id": "TuanPA48", "name": "Phùng Anh Tuấn", "chain": "FPT Shop", "pattern": ["Ca Chiều", "OFF", "Trực đêm", "OFF", "Ca Sáng", "Ca Sáng", "OFF"]},
        {"code": "32690", "id": "LuanNV8", "name": "Nguyễn Văn Luân", "chain": "FPT Shop", "pattern": ["Ca Chiều", "Ca Sáng", "Ca Chiều", "Trực đêm", "OFF", "OFF BÙ", "OFF"]},
        {"code": "51779", "id": "MinhPP2", "name": "Phạm Phú Minh", "chain": "FPT Shop", "pattern": ["OFF BÙ", "OFF PHÉP", "Ca Chiều", "Ca Sáng", "Trực đêm", "OFF", "OFF"]},
        {"code": "51784", "id": "QuyNN13", "name": "Nguyễn Ngọc Quý", "chain": "FPT Shop", "pattern": ["Ca Sáng", "Ca Chiều", "Ca Chiều", "Ca Chiều", "Trực đêm", "OFF", "OFF"]},
        {"code": "51786", "id": "TanTQ6", "name": "Trần Quang Tân", "chain": "FPT Shop", "pattern": ["Ca Sáng", "Trực đêm", "OFF", "Ca Chiều", "Ca Sáng", "Ca Sáng", "OFF"]},
        {"code": "51792", "id": "TuongPN3", "name": "Phan Ngọc Tường", "chain": "FPT Shop", "pattern": ["Ca Sáng", "Ca Chiều", "Ca Sáng", "Ca Chiều", "Trực đêm", "OFF", "OFF BÙ"]},
        {"code": "51793", "id": "BaoTDC", "name": "Trần Đức Chí Bảo", "chain": "FPT Shop", "pattern": ["Ca Sáng", "Ca Sáng", "Ca Chiều", "Ca Sáng", "Trực đêm", "OFF", "OFF"]},
        {"code": "51795", "id": "SonDQ3", "name": "Đặng Quang Sơn", "chain": "FPT Shop", "pattern": ["OFF PHÉP", "Ca Chiều", "Trực đêm", "OFF", "Ca Sáng", "OFF PHÉP", "OFF"]},
        {"code": "51796", "id": "DucNM79", "name": "Nguyễn Minh Đức", "chain": "FPT Shop", "pattern": ["Ca Chiều", "Ca Sáng", "Ca Chiều", "Trực đêm", "OFF", "Ca Sáng", "OFF"]},
        {"code": "12678", "id": "ViDNT2", "name": "Đỗ Ngọc Thúy Vi", "chain": "FPT Shop", "pattern": ["Ca Sáng", "Ca Sáng", "Trực đêm", "OFF", "Ca Sáng", "Ca Sáng", "OFF"]},
        {"code": "42372", "id": "DuyenNTM20", "name": "Nguyễn Thị Mỹ Duyên", "chain": "FPT Shop", "pattern": ["Ca Sáng", "Ca Sáng", "Ca Sáng", "OFF BÙ", "OFF BÙ", "OFF BÙ", "OFF"]},
        {"code": "51800", "id": "SangLM4", "name": "Lê Minh Sáng", "chain": "FPT Shop", "pattern": ["Trực đêm", "OFF", "Ca Sáng", "Ca Sáng", "Ca Sáng", "Sáng + đêm", "OFF"]},
        {"code": "51801", "id": "TamNT54", "name": "Nguyễn Thanh Tâm", "chain": "FPT Shop", "pattern": ["OFF BÙ", "OFF BÙ", "Ca Chiều", "Ca Sáng", "Trực đêm", "OFF", "OFF"]},
        {"code": "51803", "id": "SonTCH", "name": "Trần Công Hoàng Sơn", "chain": "FPT Shop", "pattern": ["OFF BÙ", "OFF BÙ", "Ca Chiều", "Ca Chiều", "Trực đêm", "OFF", "OFF"]},
        {"code": "100859", "id": "ThanhNN25", "name": "Nguyễn Ngọc Thanh", "chain": "FPT Shop", "pattern": ["Ca Sáng", "Trực đêm", "OFF", "Ca Chiều", "Ca Sáng", "Ca Sáng", "OFF"]},
        {"code": "111358", "id": "QuyNV34", "name": "Nguyễn Văn Quý", "chain": "FPT Shop", "pattern": ["Ca Chiều", "Ca Chiều", "Ca Sáng", "Ca Chiều", "Ca Chiều", "Sáng + đêm", "OFF"]},
        {"code": "51806", "id": "TaiVM3", "name": "Võ Minh Tài", "chain": "FPT Shop", "pattern": ["OFF", "OFF BÙ", "Ca Sáng", "Ca Sáng", "Ca Chiều", "Trực đêm", "OFF"]},
        {"code": "51808", "id": "ThongHQ3", "name": "Hồ Quốc Thông", "chain": "FPT Shop", "pattern": ["Ca Sáng", "Ca Chiều", "Ca Chiều", "Ca Sáng", "OFF", "Ca Chiều", "OFF BÙ"]},
        {"code": "51809", "id": "DatCT10", "name": "Chiêng Tấn Đạt", "chain": "FPT Shop", "pattern": ["Trực đêm", "OFF", "Ca Chiều", "Ca Sáng", "Ca Sáng", "OFF PHÉP", "Trực đêm"]},
        {"code": "51810", "id": "PhongTTH2", "name": "Trần Trương Huy Phong", "chain": "FPT Shop", "pattern": ["Trực đêm", "OFF", "Ca Chiều", "Ca Sáng", "Ca Sáng", "OFF BÙ", "Sáng + đêm"]},
        {"code": "107683", "id": "HienPN3", "name": "Phạm Ngọc Hiền", "chain": "FPT Shop", "pattern": ["OFF", "Ca Sáng", "Ca Sáng", "Ca Chiều", "Ca Sáng", "Trực đêm", "OFF"]},
        {"code": "55003", "id": "DuongNP", "name": "Nguyễn Phi Dương", "chain": "FPT Shop", "pattern": ["OFF BÙ", "Ca Chiều", "Ca Sáng", "Trực đêm", "OFF", "OFF PHÉP", "OFF"]},
        {"code": "55005", "id": "LinhLT47", "name": "Lý Thành Linh", "chain": "FPT Shop", "pattern": ["Trực đêm", "OFF", "Ca Sáng", "Ca Chiều", "Ca Chiều", "Ca Sáng", "Trực đêm"]}
    ]
    for row in sample_rows:
        for i, (d_str, dow) in enumerate(month_dates):
            shift = row["pattern"][i % len(row["pattern"])]
            obj = EmployeeShift(
                month=target_month,
                employee_id=row["id"],
                employee_code=row["code"],
                employee_name=row["name"],
                chain=row["chain"],
                date=d_str,
                shift_type=shift,
                day_of_week=dow
            )
            db.add(obj)
    db.commit()

@router.get("/schedule/matrix")
def get_schedule_matrix(month: str = Query("2026-11"), chain: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(EmployeeShift).filter(EmployeeShift.month == month)
    if chain and chain != "All":
        query = query.filter(EmployeeShift.chain == chain)
    records = query.all()
    
    if not records:
        _seed_demo_shifts_if_empty(db, target_month=month)
        records = query.all()
        
    dates_dict = {}
    employees_dict = {}
    
    for r in records:
        if r.date not in dates_dict:
            dates_dict[r.date] = r.day_of_week or ""
        if r.employee_id not in employees_dict:
            employees_dict[r.employee_id] = {
                "id": r.employee_id,
                "code": r.employee_code or "",
                "name": r.employee_name or r.employee_id,
                "chain": r.chain,
                "shifts": {}
            }
        employees_dict[r.employee_id]["shifts"][r.date] = r.shift_type
        
    sorted_dates = sorted(dates_dict.keys())
    date_headers = [{"date": d, "dayOfWeek": dates_dict[d]} for d in sorted_dates]
    employee_list = sorted(list(employees_dict.values()), key=lambda x: x["name"])
    
    return {
        "month": month,
        "dates": date_headers,
        "employees": employee_list,
        "totalEmployees": len(employee_list)
    }

