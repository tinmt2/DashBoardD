import json
import logging
import threading
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

PLAYBACK_SEMAPHORE = threading.Semaphore(4)

class FtelPlaybackScanner:
    def __init__(self):
        pass

    @staticmethod
    def decode_mask(mask: int, year: int, month: int) -> List[int]:
        """
        Decodes the Xiongmai OPCalendarQuery bitmask into a list of days.
        Bit 0 -> Day 1
        Bit 1 -> Day 2
        ...
        Bit 30 -> Day 31
        """
        if mask <= 0:
            return []
            
        import calendar
        # Get the number of days in the specified month
        _, num_days = calendar.monthrange(year, month)
        
        days = []
        for bit_index in range(32):
            if (mask >> bit_index) & 1:
                day = bit_index + 1
                if day <= num_days:
                    days.append(day)
        return days

    def get_recording_calendar(self, driver, channel_index: int, year: int, month: int) -> Dict[str, Any]:
        """
        Executes OPCalendarQuery via Web Viewer gDevice
        """
        payload = {
            "OPCalendarQuery": {
                "Channel": channel_index,
                "Event": "*",
                "Month": month,
                "Type": "h264",
                "Year": year
            }
        }
        
        script = """
            var done = arguments[arguments.length - 1];
            var dev = window.gDevice;
            
            // Search iframes if not found in top window
            if (!dev) {
                for(var i=0; i<window.frames.length; i++){
                    try {
                        if(window.frames[i].gDevice){
                            dev = window.frames[i].gDevice;
                            break;
                        }
                    } catch(e){}
                }
            }
            
            if (!dev) {
                done(JSON.stringify({error: "gDevice undefined"}));
                return;
            }
            
            var cmd = "OPCalendarQuery";
            var data = arguments[0];
            
            // Try different methods
            var handled = false;
            
            if (typeof dev.GetMsg === 'function') {
                try {
                    dev.GetMsg(3, cmd, function(resp) { done(JSON.stringify(resp)); }, data);
                    handled = true;
                } catch(e) {}
            }
            
            if (!handled && typeof dev.SendMsg === 'function') {
                try {
                    dev.SendMsg(3, cmd, data, function(resp) { done(JSON.stringify(resp)); });
                    handled = true;
                } catch(e) {}
            }
            
            if (!handled && typeof dev.SearchRecord === 'function') {
                try {
                    var req = { "Name": cmd, [cmd]: data[cmd] };
                    dev.SearchRecord(req, function(resp) { done(JSON.stringify(resp)); });
                    handled = true;
                } catch(e) {}
            }
            
            if (!handled) {
                done(JSON.stringify({error: "No suitable method found on gDevice"}));
            }
        """
        
        import time
        max_retries = 2
        for attempt in range(max_retries):
            try:
                res_str = driver.execute_async_script(script, payload)
                if not res_str:
                    return self._error_res(channel_index, year, month, "Empty response from execute_async_script")
                    
                res = json.loads(res_str)
                
                if "error" in res:
                    return self._error_res(channel_index, year, month, res["error"])
                    
                ret = res.get("Ret", -1)
                
                # If DVR is busy (-10012), sleep and retry once
                if ret == -10012 and attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                    
                if ret != 100:
                    if ret == 607:
                        return {
                            "channel": channel_index,
                            "camera": f"CH{channel_index + 1:02d}",
                            "year": year,
                            "month": month,
                            "mask": 0,
                            "recording_days": [],
                            "last_recording_day": None,
                            "ret": ret,
                            "error": None
                        }
                    return self._error_res(channel_index, year, month, f"API Error, Ret: {ret}")
                    
                mask = res.get("OPCalendarQuery", {}).get("Mask", 0)
                recording_days = self.decode_mask(mask, year, month)
                last_recording_day = recording_days[-1] if recording_days else None
                
                return {
                    "channel": channel_index,
                    "camera": f"CH{channel_index + 1:02d}",
                    "year": year,
                    "month": month,
                    "mask": mask,
                    "recording_days": recording_days,
                    "last_recording_day": last_recording_day,
                    "ret": ret,
                    "error": None
                }
                
            except Exception as e:
                return self._error_res(channel_index, year, month, str(e))
                
        return self._error_res(channel_index, year, month, "Max retries exceeded")

    def get_recording_files(self, driver, channel_index: int, begin_time: str, end_time: str) -> Dict[str, Any]:
        """
        Executes OPFileQuery via Web Viewer gDevice
        begin_time, end_time format: YYYY-MM-DD HH:MM:SS
        """
        payload = {
            "OPFileQuery": {
                "BeginTime": begin_time,
                "Channel": channel_index,
                "DriverType": 0,
                "EndTime": end_time,
                "Event": "*",
                "StreamType": 0,
                "Type": "h264"
            }
        }
        
        script = """
            var done = arguments[arguments.length - 1];
            var dev = window.gDevice;
            
            if (!dev) {
                for(var i=0; i<window.frames.length; i++){
                    try {
                        if(window.frames[i].gDevice){
                            dev = window.frames[i].gDevice;
                            break;
                        }
                    } catch(e){}
                }
            }
            
            if (!dev) {
                done(JSON.stringify({error: "gDevice undefined"}));
                return;
            }
            
            var cmd = "OPFileQuery";
            var data = arguments[0];
            
            var handled = false;
            if (typeof dev.GetMsg === 'function') {
                try {
                    dev.GetMsg(3, cmd, function(resp) { done(JSON.stringify(resp)); }, data);
                    handled = true;
                } catch(e) {}
            }
            
            if (!handled && typeof dev.SendMsg === 'function') {
                try {
                    dev.SendMsg(3, cmd, data, function(resp) { done(JSON.stringify(resp)); });
                    handled = true;
                } catch(e) {}
            }
            
            if (!handled && typeof dev.SearchRecord === 'function') {
                try {
                    var req = { "Name": cmd, [cmd]: data[cmd] };
                    dev.SearchRecord(req, function(resp) { done(JSON.stringify(resp)); });
                    handled = true;
                } catch(e) {}
            }
            
            if (!handled) {
                done(JSON.stringify({error: "No suitable method found on gDevice"}));
            }
        """
        
        try:
            res_str = driver.execute_async_script(script, payload)
            if not res_str:
                return {"channel": channel_index, "files": [], "error": "Empty response"}
                
            res = json.loads(res_str)
            if "error" in res:
                return {"channel": channel_index, "files": [], "error": res["error"]}
                
            ret = res.get("Ret", -1)
            if ret != 100:
                return {"channel": channel_index, "files": [], "error": f"API Error, Ret: {ret}"}
                
            files = res.get("OPFileQuery", [])
            return {
                "channel": channel_index,
                "files": files,
                "ret": ret,
                "error": None
            }
            
        except Exception as e:
            return {"channel": channel_index, "files": [], "error": str(e)}

    def _error_res(self, channel_index: int, year: int, month: int, err: str) -> Dict[str, Any]:
        return {
            "channel": channel_index,
            "camera": f"CH{channel_index + 1:02d}",
            "year": year,
            "month": month,
            "mask": 0,
            "recording_days": [],
            "last_recording_day": None,
            "ret": -1,
            "error": err
        }
