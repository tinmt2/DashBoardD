import pytest
import datetime
import pandas as pd
from app.services.importers.fpt_shop.mapper import ColumnMapper
from app.services.importers.fpt_shop.date_parser import FPTShopDateParser
from app.services.importers.fpt_shop.fpt_shop_error_mapping import FPTShopErrorMapping
from app.services.importers.fpt_shop.adapter import RowNormalizer
from app.services.importers.fpt_shop.validator import RecordValidator

def test_column_mapper():
    mapper = ColumnMapper()
    headers = ["Tên nhân viên", "TICKET ID", "Ngày Tạo  ", "Unknown Column"]
    mapping = mapper.map_columns(headers)
    
    assert "employee_name" in mapping
    assert mapping["employee_name"]["source_column"] == "Tên nhân viên"
    assert mapping["employee_name"]["confidence"] == 1.0
    
    assert "ticket_id" in mapping
    assert mapping["ticket_id"]["source_column"] == "TICKET ID"
    assert mapping["ticket_id"]["confidence"] == 1.0
    
    assert "created_at" in mapping
    assert mapping["created_at"]["source_column"] == "Ngày Tạo  "
    
    assert "Unknown Column" not in [v["source_column"] for v in mapping.values()]

def test_date_parser():
    parser = FPTShopDateParser()
    assert parser.parse("2026-09-28").date() == datetime.date(2026, 9, 28)
    assert parser.parse("28/09/2026 14:30") == datetime.datetime(2026, 9, 28, 14, 30)
    assert parser.parse(44800.0) is not None # Excel date
    assert parser.parse(None) is None
    assert parser.parse("invalid") is None

def test_error_mapping():
    mapper = FPTShopErrorMapping()
    assert mapper.normalize("Thiếu thông tin") == "Thiếu thông tin"
    assert mapper.normalize("   THIẾU  TT  ") == "Thiếu thông tin"
    assert mapper.normalize("Lỗi chưa biết") == "Lỗi chưa biết"
    assert mapper.normalize(None) is None

def test_row_normalizer():
    normalizer = RowNormalizer()
    mapping = {
        "ticket_id": {"source_column": "Ticket ID"},
        "employee_name": {"source_column": "Tên nhân viên"}
    }
    row = {"Ticket ID": "T123", "Tên nhân viên": "Nguyen Van A"}
    result = normalizer.normalize_row(row, mapping)
    
    assert result["ticket_id"] == "T123"
    assert result["employee_name"] == "Nguyen Van A"
    assert result["chain"] == "FPT_SHOP"
    assert result["source"] == "EXCEL"

def test_validator():
    validator = RecordValidator()
    valid_record = {
        "ticket_id": "T123",
        "employee_name": "Nguyen Van A",
        "error_status": "PASS",
        "chain": "FPT_SHOP",
        "source": "EXCEL",
        "created_at": datetime.datetime.now()
    }
    assert validator.validate(1, valid_record).is_valid == True
    
    invalid_record = dict(valid_record)
    invalid_record["ticket_id"] = ""
    res = validator.validate(2, invalid_record)
    assert res.is_valid == False
    assert res.errors[0]["field"] == "ticket_id"
