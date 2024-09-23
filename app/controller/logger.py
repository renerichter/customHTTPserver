

import datetime as dt
import json
import logging
import logging.config
import logging.handlers
from dataclasses import dataclass, field
from os import path
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, Optional, override
from uuid import uuid4

LOG_RECORD_BUILTIN_ATTRS = {"args","asctime","created","exc_info","exc_text","filename","funcName","levelname","levelno","lineno","module","msecs","message","msg","name","pathname","process","processName","relativeCreated","stack_info","thread","threadName","taskName",
}

class MyJSONFormatter(logging.Formatter):
    """Based on: https://github.com/mCodingLLC/VideosSampleCode/blob/master/videos/135_modern_logging/mylogger.py -> thank you!!!"""
    def __init__(self,*,fmt_keys: dict[str,str] | None = None):
        super().__init__()
        self.fmt_keys = fmt_keys if fmt_keys is not None else {}
        
    @override
    def format(self, record: logging.LogRecord):
        message = self._prepare_log_dict(record)
        return json.dumps(message,default=str)

    def _prepare_log_dict(self,record: logging.LogRecord):
        always_fields = {
            "message": record.getMessage(),
            "timestamp": dt.datetime.fromtimestamp(record.created, tz=dt.timezone.utc).isoformat(),
        }
        if record.exc_info is not None:
            always_fields["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info is not None:
            always_fields["stack_info"] = self.formatStack(record.stack_info)
        if hasattr(record, 'trace_context'):
            always_fields['trace_context'] = record.trace_context
        message = {key: msg_val if (msg_val := always_fields.pop(val,None)) is not None else getattr(record,val) for key,val in self.fmt_keys.items()}
        message.update(always_fields)
        

        for key, val in record.__dict__.items():
            if key not in LOG_RECORD_BUILTIN_ATTRS:
                message[key] = val

        return message


class NonErrorFilter(logging.Filter):
    @override
    def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
        return record.levelno <= logging.INFO
    
class LoggerSetup:
    def __init__(self,config_path: str, log_level:str='ERROR'):
        self.config_path = Path(config_path)
        self.queue_handler: Optional[logging.handlers.QueueHandler] = None
        self.log_level:str
        
    def setup_logging(self):
        with open(self.config_path) as f_in:
            config = json.load(f_in)
        
        logging.config.dictConfig(config)
        
        self.queue_handler = logging.getHandlerByName("queue_handler")
        if self.queue_handler and hasattr(self.queue_handler,'listener'):
            self.queue_handler.listener.start()
    
    async def stop_logging(self):
        if self.queue_handler and hasattr(self.queue_handler,'listener'):
            self.queue_handler.listener.stop()
            print("Logging queue listener stopped.")

class CustomRotatingFileHandler(logging.handlers.RotatingFileHandler):
    def getBackupName(self,n:int):
        base,ext = path.splitext(self.baseFilename)
        return f"{base}-{n}{ext}"

@dataclass
class RequestContext:
    trace_id: str = field(default_factory=lambda: str(uuid4()))
    request_method:str = ""
    request_path: str = ""
    start_time: float  = field(default_factory=perf_counter)
    response_times: Dict[str,Any] = field(default_factory=dict)
    
    def add_response_time(self,component: str, duration:float):
        self.response_times[component] = duration
    
    def to_dict(self)->Dict[str,Any]:
        return {"trace_id": self.trace_id,
                "request_method": self.request_method,
                "request_path": self.request_path,
                "total_time": perf_counter() - self.start_time,
                "response_times": self.response_times}