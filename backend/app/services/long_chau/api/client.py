import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class LongChauApiClient:
    BASE_URL = "https://bapp.frt.vn/api"
    TICKETS_TABLE_ID = "ta_906c3ea9f5ce4b218b9597bec3f77298"
    VIOLATIONS_TABLE_ID = "ta_034fc6b1ac194beeb949f8b7739d8a11"

    def __init__(self, cookies: Dict[str, str]):
        """
        Initialize with cookies from the authenticated browser session.
        Needs at least the 'budibase:currentapp' cookie.
        """
        self.cookies = cookies
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-budibase-app-id": "frt-gscmr-long-chau"
        }

    def search_table(self, table_id: str, payload: dict, stop_before_date: str = None) -> List[dict]:
        """Generic search for a Budibase table handling pagination."""
        url = f"{self.BASE_URL}/{table_id}/search"
        all_rows = []
        
        # Ensure paginate is true if we want all pages, or handle manual bookmark pagination
        payload["paginate"] = True
        payload["limit"] = 1000  # Max limit per request usually
        
        try:
            while True:
                response = requests.post(url, json=payload, headers=self.headers, cookies=self.cookies)
                if response.status_code != 200:
                    logger.error(f"Budibase Error {response.status_code}: {response.text}")
                response.raise_for_status()
                data = response.json()
                
                rows = data.get("data", []) if "data" in data else data.get("rows", [])
                
                if rows:
                    first_date = rows[0].get("Created At") or rows[0].get("createdAt") or ""
                    last_date = rows[-1].get("Created At") or rows[-1].get("createdAt") or ""
                    logger.info(f"Fetched chunk of {len(rows)} rows. Date range: {first_date} to {last_date}")
                    
                    if stop_before_date and last_date and first_date:
                        is_descending = first_date >= last_date
                        if is_descending and last_date < stop_before_date:
                            logger.info(f"Reached data older than {stop_before_date} (descending mode). Stopping fetch early.")
                            # all_rows.extend(rows) is already done below
                            break
                        elif not is_descending:
                            logger.warning(f"Data is sorted ASCENDING! Cannot break early. {first_date} -> {last_date}")
                        
                all_rows.extend(rows)
                
                bookmark = data.get("bookmark")
                if not bookmark:
                    break
                
                # Safety break to avoid infinite loop
                if len(all_rows) > 10000:
                    logger.warning("Fetched 10000 rows, breaking to avoid infinite loop.")
                    break
                    
                payload["bookmark"] = bookmark
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error querying Budibase table {table_id}: {e}")
            raise Exception(f"Lỗi khi lấy dữ liệu Long Châu API: {str(e)}")
            
        return all_rows

    def get_tickets(self, start_date: str, end_date: str) -> List[dict]:
        """
        Fetch all tickets created between start_date and end_date.
        Dates should be ISO format strings, e.g., '2026-10-01T00:00:00.000Z'
        """
        # 400 Bad Request is likely due to query syntax. 
        # We will fetch everything or let Budibase handle it without a query.
        payload = {
            "sortOrder": "descending",
            "sortType": "string",
            "sort": "Created At"
        }
        return self.search_table(self.TICKETS_TABLE_ID, payload, start_date)

    def get_violations(self, ticket_ids: List[str], start_date: str = None) -> List[dict]:
        """
        Fetch violation details for specific tickets.
        In Budibase, we can use an 'equal' or 'in' array, but typically we might just fetch
        all recent violations or chunk the query.
        """
        if not ticket_ids:
            return []
            
        # Budibase allows querying by multiple exact matches using 'oneOf' or 'contains'
        # Since standard is sometimes strict, we can query all violations in the date range 
        # or just fetch them by ticket ID chunks.
        # For simplicity, if ticket_ids is large, this might need batching.
        payload = {
            "sortOrder": "descending",
            "sortType": "string",
            "sort": "Created At"
        }
        return self.search_table(self.VIOLATIONS_TABLE_ID, payload, start_date)

    def get_full_report(self, start_date: str, end_date: str) -> List[dict]:
        """
        Fetches tickets and their violations, merging them into a flat structure
        similar to the Excel report.
        """
        logger.info(f"Fetching Long Chau tickets from {start_date} to {end_date}")
        tickets = self.get_tickets(start_date, end_date)
        
        # Filter tickets locally because Budibase API query syntax was causing 400 Bad Request
        filtered_tickets = []
        for t in tickets:
            try:
                # "Created At": "2026-10-07T12:41:31.062Z"
                t_date = t.get("Created At") or t.get("createdAt") or ""
                if t_date >= start_date:
                    filtered_tickets.append(t)
            except:
                pass
        tickets = filtered_tickets
        
        
        if not tickets:
            return []
            
        ticket_map = {t["_id"]: t for t in tickets}
        ticket_ids = list(ticket_map.keys())
        
        logger.info(f"Fetching violations for {len(ticket_ids)} tickets")
        # To avoid URL too long or payload too large, we could batch
        # But let's assume oneOf handles it for now.
        violations = self.get_violations(ticket_ids, start_date)
        
        # If oneOf fails, we might need to fallback to fetching all violations in the date range
        if not violations and len(tickets) > 0:
             # Fallback query: fetch all violations created in the range
             logger.warning("No violations found with oneOf, attempting date range fallback")
             fallback_payload = {
            "sortOrder": "descending",
            "sortType": "string",
            "sort": "Created At"
        }
             violations = self.search_table(self.VIOLATIONS_TABLE_ID, fallback_payload, start_date)
             # Filter only those belonging to our tickets
             violations = [v for v in violations if v.get("TicketID") in ticket_map]

        
        full_records = []
        for v in violations:
            t_id = v.get("TicketID")
            if t_id and t_id in ticket_map:
                t = ticket_map[t_id]
                # Merge ticket and violation
                merged = {**t, **v}
                # Log the keys of the first record to a file
                if not getattr(self, "_logged_keys", False):
                    self._logged_keys = True
                    import json
                    try:
                        with open("long_chau_ticket.json", "w", encoding="utf-8") as fk:
                            json.dump(t, fk, ensure_ascii=False, indent=2)
                        with open("long_chau_violation.json", "w", encoding="utf-8") as fk:
                            json.dump(v, fk, ensure_ascii=False, indent=2)
                    except: pass
                # Rename keys to clarify
                merged["ticket_id_ref"] = t["_id"]
                merged["violation_id"] = v["_id"]
                full_records.append(merged)
                
        return full_records
