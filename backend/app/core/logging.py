import logging
import os
from collections import deque
from datetime import datetime
from logging.handlers import RotatingFileHandler

LOG_BUFFER = deque(maxlen=2000)

class MemoryLogHandler(logging.Handler):
    def emit(self, record):
        try:
            entry = {
                "id": f"{record.created}_{len(LOG_BUFFER)}",
                "timestamp": datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S"),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage()
            }
            LOG_BUFFER.append(entry)
        except Exception:
            pass

_memory_handler = MemoryLogHandler()
_memory_handler.setLevel(logging.INFO)

def setup_logging():
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    _memory_handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    if _memory_handler not in root_logger.handlers:
        root_logger.addHandler(_memory_handler)
        
    # Also write to app.log in backend directory
    try:
        log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "app.log"))
        file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=2, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)
    except Exception:
        pass
        
    return logging.getLogger("opsmonitor")

logger = logging.getLogger("opsmonitor")

def get_recent_logs(lines: int = 200, level: str = None, search: str = None):
    items = list(LOG_BUFFER)
    if level and level.upper() != "ALL":
        items = [i for i in items if i["level"].upper() == level.upper()]
    if search:
        s = search.lower().strip()
        items = [i for i in items if s in i["message"].lower() or s in i["logger"].lower()]
    return items[-lines:]

def clear_memory_logs():
    LOG_BUFFER.clear()
