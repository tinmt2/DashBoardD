import unittest
from unittest.mock import MagicMock
import json

import sys
sys.path.insert(0, r"D:\Tín\ABC\test")
from app.services.ftel_playback_service import FtelPlaybackScanner

class TestFtelPlaybackScanner(unittest.TestCase):
    def setUp(self):
        self.scanner = FtelPlaybackScanner()
        self.driver = MagicMock()

    def test_case_1_mask_201326592(self):
        # Mask 201326592 corresponds to days 27 and 28
        days = self.scanner.decode_mask(201326592, 2026, 9)
        self.assertEqual(days, [27, 28])

    def test_case_2_mask_0(self):
        days = self.scanner.decode_mask(0, 2026, 9)
        self.assertEqual(days, [])

    def test_case_3_mask_1(self):
        # Bit 0 -> Day 1
        days = self.scanner.decode_mask(1, 2026, 9)
        self.assertEqual(days, [1])

    def test_case_4_multiple_days(self):
        # Day 1 (1) + Day 3 (4) + Day 5 (16) = 21
        days = self.scanner.decode_mask(21, 2026, 9)
        self.assertEqual(days, [1, 3, 5])

    def test_case_out_of_month_bounds(self):
        # Month 2 (Feb) in 2026 has 28 days
        # Bit 30 -> Day 31 -> 2^30 = 1073741824
        # It should ignore day 31
        days = self.scanner.decode_mask(1073741824, 2026, 2)
        self.assertEqual(days, [])

    def test_case_5_ret_not_100(self):
        self.driver.execute_async_script.return_value = json.dumps({"Ret": -10006})
        res = self.scanner.get_recording_calendar(self.driver, 0, 2026, 9)
        self.assertIsNotNone(res["error"])
        self.assertIn("API Error", res["error"])
        self.assertEqual(res["recording_days"], [])

    def test_case_6_gdevice_undefined(self):
        self.driver.execute_async_script.return_value = json.dumps({"error": "gDevice undefined"})
        res = self.scanner.get_recording_calendar(self.driver, 0, 2026, 9)
        self.assertEqual(res["error"], "gDevice undefined")

    def test_case_7_opfilequery_payload(self):
        # Ensure DriverType and StreamType are in the payload sent to execute_async_script
        self.driver.execute_async_script.return_value = json.dumps({"Ret": 100, "OPFileQuery": []})
        self.scanner.get_recording_files(self.driver, 0, "2026-09-28 00:00:00", "2026-09-28 23:59:59")
        
        # Get the payload passed as the second argument
        args, kwargs = self.driver.execute_async_script.call_args
        payload = args[1]
        
        self.assertIn("OPFileQuery", payload)
        self.assertIn("DriverType", payload["OPFileQuery"])
        self.assertIn("StreamType", payload["OPFileQuery"])
        self.assertEqual(payload["OPFileQuery"]["DriverType"], 0)
        self.assertEqual(payload["OPFileQuery"]["StreamType"], 0)

if __name__ == '__main__':
    unittest.main()
