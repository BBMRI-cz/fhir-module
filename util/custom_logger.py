import json
import logging
import logging.config
import os
import sys

import yaml

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger(__name__)


class JsonFormatter(logging.Formatter):
    """JSON log formatter for structured logging.

    If the log message is a valid JSON object, its fields are merged into
    the top-level log entry (e.g. sync_summary becomes a direct field).
    Otherwise the message is stored under the "message" key.
    """

    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "logger": record.name,
            "level": record.levelname,
        }

        message = record.getMessage()
        try:
            parsed = json.loads(message)
            if isinstance(parsed, dict):
                log_entry.update(parsed)
            else:
                log_entry["message"] = message
        except (json.JSONDecodeError, TypeError):
            log_entry["message"] = message

        return json.dumps(log_entry)


def is_running_tests():
    return (
        'pytest' in sys.modules or 
        'unittest' in sys.modules or
        'pytest' in sys.argv[0] or
        any('test' in arg for arg in sys.argv)
    )


def setup_logger():
    # Use different logging config for tests
    if is_running_tests():
        config_file_name = 'logging_test.yaml'
    else:
        config_file_name = 'logging.yaml'
    
    config_path = os.path.join(ROOT_DIR, config_file_name)
    
    with open(config_path, 'r') as config_file:
        log_cfg = yaml.safe_load(config_file.read())
        if "root" in log_cfg:
            log_cfg["root"]["level"] = os.getenv("LOG_LEVEL","DEBUG").upper()

        log_dir = os.getenv("LOG_DIR", "/var/log/fhir-module")
        os.makedirs(log_dir, exist_ok=True)
        for handler in log_cfg.get("handlers", {}).values():
            if "filename" in handler:
                filename = os.path.basename(handler["filename"])
                handler["filename"] = os.path.join(log_dir, filename)

        logging.config.dictConfig(log_cfg)
