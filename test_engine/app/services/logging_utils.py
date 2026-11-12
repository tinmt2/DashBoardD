import logging
import json
import traceback
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime
import contextvars

from app.paths import LOGS_DIR, ensure_runtime_dirs

# Context variables for tracing
session_id_var = contextvars.ContextVar("session_id", default=None)
action_id_var = contextvars.ContextVar("action_id", default=None)
job_id_var = contextvars.ContextVar("job_id", default=None)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).astimezone().isoformat(),
            "level": record.levelname,
            "layer": "backend",
            "event": getattr(record, "event", "LOG"),
            "message": record.getMessage(),
            "module": record.name
        }
        
        session_id = session_id_var.get()
        if session_id:
            log_entry["session_id"] = session_id
            
        action_id = action_id_var.get()
        if action_id:
            log_entry["action_id"] = action_id
            
        job_id = job_id_var.get()
        if job_id:
            log_entry["job_id"] = job_id
            
        # Add metadata
        metadata = getattr(record, "metadata", {})
        if metadata:
            log_entry["metadata"] = metadata
            
        if record.exc_info:
            log_entry["error_type"] = record.exc_info[0].__name__ if record.exc_info[0] else "UnknownError"
            log_entry["error_message"] = str(record.exc_info[1])
            log_entry["stack_trace"] = "".join(traceback.format_exception(*record.exc_info))
            
        # Redact sensitive fields if any in metadata
        self._redact(log_entry)
            
        return json.dumps(log_entry, ensure_ascii=False)
        
    def _redact(self, obj):
        sensitive_keys = {"password", "token", "access_token", "refresh_token", "cookie", "authorization"}
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k.lower() in sensitive_keys:
                    obj[k] = "***REDACTED***"
                elif isinstance(v, (dict, list)):
                    self._redact(v)
        elif isinstance(obj, list):
            for item in obj:
                self._redact(item)

def setup_logging(level: int = None) -> None:
    if level is None:
        import os
        env_level = os.getenv("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, env_level, logging.INFO)
        
    ensure_runtime_dirs()
    
    # Base filename is backend.log, rotation adds .YYYY-MM-DD
    log_file = Path(LOGS_DIR) / "backend.log"

    # Daily rotation, keep 14 days
    file_handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=14,
        encoding="utf-8"
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setFormatter(JsonFormatter())
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JsonFormatter())
    
    # We remove existing handlers from root to avoid duplicate logs
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    logging.basicConfig(
        level=level,
        handlers=[file_handler, console_handler],
        force=True,
    )

def get_logger(name: str):
    return logging.getLogger(name)
