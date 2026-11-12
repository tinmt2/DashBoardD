import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from app.services import gsheet_sync

class TestGSheetSyncBugfix(unittest.TestCase):
    
    @patch('app.services.gsheet_sync._get_worksheet')
    @patch('app.services.gsheet_sync.get_client')
    def test_update_ticket_status_by_id_row_matching(self, mock_get_client, mock_get_worksheet):
        mock_ws = MagicMock()
        mock_get_worksheet.return_value = mock_ws
        
        # Mock GSheet data (DVR format)
        # Column A=0, B=1, C=2, D=3, E=4, F=5 (Ticket), G=6, H=7, I=8
        mock_ws.get_all_values.return_value = [
            ["Vùng", "Unnamed", "Mã shop", "Tên shop", "Unnamed_2", "Ticket", "Unnamed_3", "Unnamed_4", "Trạng thái xử lý"],
            ["MT", "", "123", "Shop A", "", "TK-01", "", "", "Offline"],
            ["HCM", "", "456", "Shop B", "", " TK-02 ", "", "", "Offline"], # Test whitespace
            ["MB", "", "789", "Shop C", "", "TK-03", "", "", "Offline"]
        ]
        
        ticket_results_map = {
            "TK-01": "Đã xử lý | Lỗi đầu ghi",
            "TK-02": "Check cam | Lỗi ổ cứng",
            "TK-NONEXISTENT": "Should not write"
        }
        
        # Call the new function
        ok, msg = gsheet_sync.update_ticket_status_by_id(
            ticket_results_map=ticket_results_map,
            sheet_name=gsheet_sync.SHEET_DVR,
            col_letter="G",
            ticket_col_index=6, # 1-based, so F
            logger=print
        )
        
        self.assertTrue(ok)
        mock_ws.batch_update.assert_called_once()
        args, kwargs = mock_ws.batch_update.call_args
        updates = args[0]
        
        # Should only have 2 updates (TK-01, TK-02)
        self.assertEqual(len(updates), 2)
        
        # Check precise row targeting
        # Row index in get_all_values: TK-01 is at index 1 -> sheet row 2
        # TK-02 is at index 2 -> sheet row 3
        self.assertEqual(updates[0]['range'], "G2")
        self.assertEqual(updates[0]['values'], [["Đã xử lý | Lỗi đầu ghi"]])
        
        self.assertEqual(updates[1]['range'], "G3")
        self.assertEqual(updates[1]['values'], [["Check cam | Lỗi ổ cứng"]])

if __name__ == '__main__':
    unittest.main()
