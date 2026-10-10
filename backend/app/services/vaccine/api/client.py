import logging
import requests
import json
import urllib.parse
from typing import Dict, Optional
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)

class VaccineApiClient:
    def __init__(self, cookies: Dict[str, str], headers: Optional[Dict[str, str]] = None):
        """
        Initialize with cookies and headers from the authenticated browser session.
        """
        self.cookies = cookies
        self.headers = headers or {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-budibase-app-id": settings.VACCINE_APP_ID
        }

    def fetch_export_report(self, start_date: str, end_date: str) -> bytes:
        """
        Fetches the real-time report for Vaccine using the internal Budibase query.
        Returns the raw XML bytes (the Excel file content).
        start_date and end_date should be in ISO format. If YYYY-MM-DD, converts them.
        """
        url = settings.VACCINE_API_ENDPOINT
        
        # Ensure correct date format
        if len(start_date) == 10:
            start_date = f"{start_date}T00:00:00.000Z"
        if len(end_date) == 10:
            end_date = f"{end_date}T23:59:59.000Z"
            
        payload = {
            "parameters": {
                "startDate": start_date,
                "endDate": end_date
            }
        }
        
        try:
            logger.info(f"[VACCINE_API] Fetching report from {url} for {start_date} to {end_date}")
            response = requests.post(url, json=payload, headers=self.headers, cookies=self.cookies)
            if response.status_code != 200:
                logger.error(f"Budibase Error {response.status_code}: {response.text}")
            response.raise_for_status()
            
            res_json = response.json()
            if not res_json.get('data') or len(res_json['data']) == 0:
                logger.warning("[VACCINE_API] Empty data array in response.")
                return b""
            
            export_value = res_json['data'][0].get('value', '')
            if not export_value.startswith('data:text/xls'):
                logger.error("[VACCINE_API] Unrecognized export format.")
                return b""
            
            # Extract the actual data part after the comma
            data_part = export_value.split(',', 1)[1]
            decoded_str = urllib.parse.unquote(data_part)
            
            logger.info(f"[VACCINE_API] Successfully decoded report, length: {len(decoded_str)}")
            return decoded_str.encode('utf-8')
            
        except Exception as e:
            logger.error(f"[VACCINE_API] Fetch failed: {str(e)}")
            raise e
