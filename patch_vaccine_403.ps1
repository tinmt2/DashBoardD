import sys

with open('backend/app/api/vaccine.py', 'r', encoding='utf-8') as f:
    content = f.read()

replacement = """    res = sync_vaccine_data(db, cookies, headers, req.start_date, req.end_date)
    if not res.get("success"):
        msg = str(res.get("message"))
        if "403" in msg or "401" in msg or "Forbidden" in msg or "Unauthorized" in msg:
            session.cached_cookies = None
            session.cached_headers = None
            session.status = "STOPPED"
            raise HTTPException(status_code=401, detail="Phiên đăng nhập Vaccine đã hết hạn, vui lòng click biểu tượng chìa khóa / refresh để đăng nhập lại.")
        raise HTTPException(status_code=500, detail=msg)"""

content = content.replace(
    '    res = sync_vaccine_data(db, cookies, headers, req.start_date, req.end_date)\n    if not res.get("success"):\n        raise HTTPException(status_code=500, detail=res.get("message"))',
    replacement
)

with open('backend/app/api/vaccine.py', 'w', encoding='utf-8') as f:
    f.write(content)

