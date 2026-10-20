from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.employee import Employee, EmployeeTransferHistory

router = APIRouter()

DEFAULT_EMPLOYEES = [
    {"id": "LuanNV8", "name": "Nguyễn Văn Luân", "chain": "FPT Shop", "status": "Active"},
    {"id": "MinhPP2", "name": "Phạm Phú Minh", "chain": "FPT Shop", "status": "Active"},
    {"id": "QuyNN13", "name": "Nguyễn Ngọc Quý", "chain": "FPT Shop", "status": "Active"},
    {"id": "TanTQ6", "name": "Trần Quang Tân", "chain": "FPT Shop", "status": "Active"},
    {"id": "TuongPN3", "name": "Phan Ngọc Tường", "chain": "FPT Shop", "status": "Active"},
    {"id": "BaoTDC", "name": "Trần Đức Chí Bảo", "chain": "FPT Shop", "status": "Active"},
    {"id": "SonDQ3", "name": "Đặng Quang Sơn", "chain": "FPT Shop", "status": "Active"},
    {"id": "DucNM79", "name": "Nguyễn Minh Đức", "chain": "FPT Shop", "status": "Active"},
    {"id": "ViDNT2", "name": "Đỗ Ngọc Thúy Vi", "chain": "FPT Shop", "status": "Active"},
    {"id": "DuyenNTM20", "name": "Nguyễn Thị Mỹ Duyên", "chain": "FPT Shop", "status": "Active"},
    {"id": "SangLM4", "name": "Lê Minh Sáng", "chain": "FPT Shop", "status": "Active"},
    {"id": "TamNT54", "name": "Nguyễn Thanh Tâm", "chain": "FPT Shop", "status": "Active"},
    {"id": "SonTCH", "name": "Trần Công Hoàng Sơn", "chain": "FPT Shop", "status": "Active"},
    {"id": "ThanhNN25", "name": "Nguyễn Ngọc Thanh", "chain": "FPT Shop", "status": "Active"},
    {"id": "QuyNV34", "name": "Nguyễn Văn Quý", "chain": "FPT Shop", "status": "Active"},
    {"id": "TaiVM3", "name": "Võ Minh Tài", "chain": "FPT Shop", "status": "Active"},
    {"id": "ThongHQ3", "name": "Hồ Quốc Thông", "chain": "FPT Shop", "status": "Active"},
    {"id": "DatCT10", "name": "Chiêng Tấn Đạt", "chain": "FPT Shop", "status": "Active"},
    {"id": "PhongTTH2", "name": "Trần Trương Huy Phong", "chain": "FPT Shop", "status": "Active"},
    {"id": "HienPN3", "name": "Phạm Ngọc Hiền", "chain": "FPT Shop", "status": "Active"},
    {"id": "DuongNP", "name": "Nguyễn Phi Dương", "chain": "FPT Shop", "status": "Active"},
    {"id": "LinhLT47", "name": "Lý Thành Linh", "chain": "FPT Shop", "status": "Active"},
    {"id": "DuanHX", "name": "Hoàng Xuân Duẩn", "chain": "FPT Shop", "status": "Active"},
    {"id": "NhanDT27", "name": "Dương Thành Nhân", "chain": "FPT Shop", "status": "Active"},
    {"id": "TuNM35", "name": "Nguyễn Minh Tú", "chain": "FPT Shop", "status": "Active"},
    {"id": "TamNM25", "name": "Nguyễn Minh Tâm", "chain": "FPT Shop", "status": "Active"},
    {"id": "VyTTH6", "name": "Tạ Trần Hà Vy", "chain": "FPT Shop", "status": "Active"},
    {"id": "MyPTK4", "name": "Phạm Thị Kiều My", "chain": "FPT Shop", "status": "Active"},
    {"id": "NgocTB35", "name": "Trác Bảo Ngọc", "chain": "FPT Shop", "status": "Active"},
    {"id": "TamLM10", "name": "Lê Minh Tâm", "chain": "FPT Shop", "status": "Active"},
    {"id": "SonTT37", "name": "Trần Thiện Sơn", "chain": "FPT Shop", "status": "Active"},
    {"id": "AnHSH2", "name": "Hứa Sang Hoàng Ân", "chain": "FPT Shop", "status": "Active"},
    {"id": "DinhLV8", "name": "Lý Văn Định", "chain": "FPT Shop", "status": "Active"},
]

def _seed_if_empty(db: Session):
    count = db.query(Employee).count()
    if count == 0:
        for item in DEFAULT_EMPLOYEES:
            emp = Employee(
                id=item["id"],
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
    name: str
    chain: str
    position: Optional[str] = ""
    status: Optional[str] = "Active"
    startDate: Optional[str] = ""

class EmployeeUpdateRequest(BaseModel):
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
