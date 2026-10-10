import pandas as pd
import io
from typing import Dict, Any, List, Tuple
from app.services.importers.fpt_shop.mapper import ColumnMapper
from app.services.importers.fpt_shop.adapter import RowNormalizer
from app.services.importers.fpt_shop.validator import RecordValidator
from app.schemas.ticket import TicketRecord

class FPTShopExcelImporter:
    def __init__(self):
        self.mapper = ColumnMapper()
        self.normalizer = RowNormalizer()
        self.validator = RecordValidator()

    def process_file(self, file_content: bytes) -> Tuple[List[TicketRecord], List[Dict], Dict[str, Any]]:
        df = pd.read_excel(io.BytesIO(file_content))
        headers = list(df.columns)
        
        mapping = self.mapper.map_columns(headers)
        
        valid_records = []
        errors = []
        
        for idx, row in df.iterrows():
            row_dict = row.to_dict()
            normalized_dict = self.normalizer.normalize_row(row_dict, mapping)
            
            validation_result = self.validator.validate(idx + 2, normalized_dict)
            
            if validation_result.is_valid:
                valid_records.append(TicketRecord(**normalized_dict))
            else:
                errors.extend(validation_result.errors)
                
        return valid_records, errors, mapping
