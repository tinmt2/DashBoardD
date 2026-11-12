from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock
import asyncio
import os
import time
import pandas as pd
from fastapi import UploadFile

from app.api.routes.ticket_router import (
    create_check_ticket_job, 
    get_ticket_job,
    cancel_ticket_job,
    JOB_STORE
)

class DummyFile:
    def __init__(self, filename="dummy.xlsx"):
        self.filename = filename
    async def read(self):
        return b"dummy data"

class TestCheckTicketLifecycle(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        JOB_STORE.clear()

    @patch("app.api.routes.ticket_router.CheckTicketScanner")
    @patch("app.api.routes.ticket_router.pd.read_excel")
    async def test_job_completed_lifecycle(self, mock_read_excel, mock_scanner_class):
        mock_read_excel.return_value = pd.DataFrame({"Ticket ID": ["123", "456"]})
        
        mock_worker = MagicMock()
        def fake_run():
            mock_worker.on_progress(1, 2)
            time.sleep(0.1)
            mock_worker.on_progress(2, 2)
            mock_worker.on_finished({
                "success": True,
                "output_file": {"available": True, "filename": "dummy_CHECK_KQ.xlsx"},
                "message": "Done"
            })
        mock_worker.run.side_effect = fake_run
        mock_scanner_class.return_value = mock_worker

        res = await create_check_ticket_job(file=DummyFile(), ticket_type="Camera MKN")
        job_id = res.data["job_id"]
        
        self.assertIn(job_id, JOB_STORE)
        
        state_res = await get_ticket_job(job_id)
        self.assertEqual(state_res.data["status"], "running")
        
        await asyncio.sleep(0.5)
        
        state_res = await get_ticket_job(job_id)
        data = state_res.data
        self.assertEqual(data["status"], "completed")
        self.assertTrue(data["success"])
        self.assertEqual(data["progress"], 2)
        self.assertEqual(data["total"], 2)
        self.assertTrue(data["output_file"]["available"])
        self.assertEqual(data["output_file"]["filename"], "dummy_CHECK_KQ.xlsx")
        self.assertNotIn("_worker", JOB_STORE[job_id])

    @patch("app.api.routes.ticket_router.CheckTicketScanner")
    @patch("app.api.routes.ticket_router.pd.read_excel")
    async def test_job_exception_stuck_running_regression(self, mock_read_excel, mock_scanner_class):
        mock_read_excel.return_value = pd.DataFrame({"Ticket ID": ["123", "456"]})
        
        mock_worker = MagicMock()
        def fake_run():
            time.sleep(0.1)
            raise ValueError("Something went terribly wrong inside the worker!")
        mock_worker.run.side_effect = fake_run
        mock_scanner_class.return_value = mock_worker

        res = await create_check_ticket_job(file=DummyFile(), ticket_type="Camera MKN")
        job_id = res.data["job_id"]
        
        await asyncio.sleep(0.5)
        
        state_res = await get_ticket_job(job_id)
        data = state_res.data
        self.assertEqual(data["status"], "failed", "Regression: Job stuck in running state after exception!")
        self.assertFalse(data["success"])
        self.assertIsNotNone(data["error"])
        self.assertEqual(data["error"]["code"], "RUNTIME_ERROR")
        self.assertIn("Something went terribly wrong", data["error"]["message"])
        self.assertNotIn("_worker", JOB_STORE[job_id])

    @patch("app.api.routes.ticket_router.CheckTicketScanner")
    @patch("app.api.routes.ticket_router.pd.read_excel")
    async def test_cancel_job(self, mock_read_excel, mock_scanner_class):
        mock_read_excel.return_value = pd.DataFrame({"Ticket ID": ["123"]})
        mock_worker = MagicMock()
        def fake_run():
            while mock_worker.is_running:
                time.sleep(0.1)
        
        mock_worker.is_running = True
        mock_worker.run.side_effect = fake_run
        mock_scanner_class.return_value = mock_worker

        res = await create_check_ticket_job(file=DummyFile(), ticket_type="Camera MKN")
        job_id = res.data["job_id"]
        
        await cancel_ticket_job(job_id)
        mock_worker.is_running = False
        
        await asyncio.sleep(0.5)
        
        state_res = await get_ticket_job(job_id)
        data = state_res.data
        self.assertEqual(data["status"], "cancelled")
        self.assertNotIn("_worker", JOB_STORE[job_id])

    @patch("app.api.routes.ticket_router.CheckTicketScanner")
    @patch("app.api.routes.ticket_router.pd.read_excel")
    async def test_single_job_lock(self, mock_read_excel, mock_scanner_class):
        mock_read_excel.return_value = pd.DataFrame({"Ticket ID": ["123"]})
        mock_worker = MagicMock()
        def fake_run():
            time.sleep(0.5); mock_worker.on_finished({})
        mock_worker.run.side_effect = fake_run
        mock_scanner_class.return_value = mock_worker

        res1 = await create_check_ticket_job(file=DummyFile(), ticket_type="Camera MKN")
        
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as context:
            await create_check_ticket_job(file=DummyFile(), ticket_type="Camera MKN")
        
        self.assertEqual(context.exception.status_code, 409)
        self.assertIn("already running", context.exception.detail)
        
        await asyncio.sleep(1.0)
        
        res2 = await create_check_ticket_job(file=DummyFile(), ticket_type="Camera MKN")
        self.assertIn("job_id", res2.data)

if __name__ == "__main__":
    unittest.main()

