from datetime import datetime
from typing import Optional, Union
import pandas as pd

class FPTShopDateParser:
    def parse(self, raw_date: Union[str, float, int, datetime, None]) -> Optional[datetime]:
        if pd.isna(raw_date) or raw_date is None or str(raw_date).strip() == "":
            return None
            
        if isinstance(raw_date, datetime):
            return raw_date
            
        try:
            # If it's a numeric excel date
            if isinstance(raw_date, (float, int)):
                parsed = pd.to_datetime(raw_date, unit='D', origin='1899-12-30')
                return parsed.to_pydatetime()
            
            parsed = pd.to_datetime(raw_date, dayfirst=True, errors='raise')
            if pd.isna(parsed):
                return None
            return parsed.to_pydatetime()
        except Exception:
            pass
            
        # Fallback for manual parsing
        str_date = str(raw_date).strip()
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y",
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y %H:%M:%S",
            "%d-%m-%Y",
            "%d-%m-%Y %H:%M",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(str_date, fmt)
            except ValueError:
                continue
                
        return None
