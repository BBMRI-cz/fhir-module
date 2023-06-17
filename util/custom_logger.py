import logging
import os

import yaml
import logging.config

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def setup_logger():
    with open(os.path.join(ROOT_DIR, 'logging.yaml'), 'r') as f:
        log_cfg = yaml.safe_load(f.read())
        logging.config.dictConfig(log_cfg)
