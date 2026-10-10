from sqlalchemy import Column, Date, DateTime, Integer, String, Text

from app.core.database import Base


class VaccineTicketDetail(Base):
    __tablename__ = "vaccine_ticket_details"

    # 1:1 with tickets.id
    ticket_record_id = Column(String, primary_key=True, index=True)
    chain = Column(String, nullable=False, index=True)
    ticket_id = Column(String, nullable=False, index=True)  # MÃ YÊU CẦU
    dedup_key = Column(String, nullable=False, unique=True, index=True)

    request_group = Column(String, nullable=True)  # NHÓM YÊU CẦU
    requester = Column(String, nullable=True)  # NGƯỜI YÊU CẦU
    handler_department = Column(String, nullable=True)  # SHOP/PHÒNG BAN XỬ LÝ
    approver = Column(String, nullable=True)  # NGƯỜI DUYỆT
    expected_completion_date = Column(Date, nullable=True)  # NGÀY DỰ KIẾN HOÀN THÀNH
    step = Column(String, nullable=True)  # BƯỚC
    region = Column(String, nullable=True)  # VÙNG MIỀN SHOP
    asm = Column(String, nullable=True)  # ASM SHOP
    camera_count = Column(String, nullable=True)  # SỐ CAMERA
    evidence_urls = Column(Text, nullable=True)  # HÌNH LỖI
    vaccine_type = Column(String, nullable=True) # LOẠI VACCINE
    violation_content = Column(String, nullable=True) # NỘI DUNG VI PHẠM
    punishment = Column(String, nullable=True) # MỨC XỬ LÝ
    employee_raw = Column(String, nullable=True)  # NHÂN VIÊN VI PHẠM
    requested_date = Column(Date, nullable=True)  # NGÀY YÊU CẦU
    step_status = Column(String, nullable=True)  # TRẠNG THÁI BƯỚC
    summary = Column(String, nullable=True) # TỔNG KẾT
    video_urls = Column(Text, nullable=True) # VIDEO LỖI
    injection_ticket_code = Column(String, nullable=True) # MÃ PHIẾU TIÊM

    import_id = Column(String, nullable=True, index=True)
    source_row = Column(Integer, nullable=True)


class VaccineImportJob(Base):
    __tablename__ = "vaccine_import_jobs"

    id = Column(String, primary_key=True, index=True)
    chain = Column(String, nullable=False)
    filename = Column(String)
    file_format = Column(String, nullable=True)
    sheet_name = Column(String, nullable=True)
    created_at = Column(DateTime)
    committed_at = Column(DateTime, nullable=True)

    total_rows = Column(Integer, default=0)
    valid_rows = Column(Integer, default=0)
    warning_rows = Column(Integer, default=0)
    error_rows = Column(Integer, default=0)
    new_rows = Column(Integer, default=0)  # rows actually inserted on commit ("success rows")
    duplicate_rows = Column(Integer, default=0)

    # CREATED, PARSING, PREVIEW_READY, COMMITTING, COMPLETED, FAILED
    status = Column(String)
    error_message = Column(String, nullable=True)
    preview_data = Column(Text, nullable=True)  # committable rows (JSON), cleared after commit
