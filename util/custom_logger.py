import logging
import logging.config
import os
import sys

import yaml

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger(__name__)


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
        logging.config.dictConfig(log_cfg)
