import logging
from sqlalchemy.orm import Session
from app.services.vaccine.api.client import VaccineApiClient
from app.services.vaccine.service import VaccineImportService

logger = logging.getLogger(__name__)

def sync_vaccine_data(db: Session, cookies: dict, headers: dict, start_date: str, end_date: str) -> dict:
    """
    Downloads the real-time Vaccine report and imports it into the DB.
    """
    try:
        client = VaccineApiClient(cookies, headers)
        logger.info(f"Starting Vaccine data sync from {start_date} to {end_date}")
        
        # 1. Fetch raw XML content
        xml_bytes = client.fetch_export_report(start_date, end_date)
        if not xml_bytes:
            return {"success": False, "message": "No data returned from Vaccine API."}
            
        # 2. Use VaccineService to preview and process the file
        service = VaccineImportService(db)
        logger.info("Parsing fetched Vaccine report...")
        preview_res = service.preview("vaccine_api_sync.xls", xml_bytes)
        
        if not preview_res.get("success"):
            return {"success": False, "message": preview_res.get("error", "Failed to parse API data")}
            
        import_id = preview_res.get("importId")
        if not import_id:
            return {"success": False, "message": "Failed to generate import job for API data"}
            
        # 3. Commit the parsed rows to DB
        logger.info(f"Committing API sync job {import_id}...")
        commit_res = service.commit(import_id)
        
        if not commit_res.get("success"):
            return {"success": False, "message": commit_res.get("error", "Failed to commit API data")}
            
        summary = commit_res.get("summary", {})
        inserted = summary.get("inserted", 0)
        duplicates = summary.get("duplicates", 0)
        
        logger.info(f"Vaccine sync complete. Inserted: {inserted}, Duplicates ignored: {duplicates}")
        return {
            "success": True,
            "inserted": inserted,
            "duplicates": duplicates
        }
        
    except Exception as e:
        logger.error(f"Vaccine sync failed: {str(e)}", exc_info=True)
        return {"success": False, "message": str(e)}
