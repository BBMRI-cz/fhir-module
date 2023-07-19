import logging
import logging.config
import os

import yaml

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger(__name__)


def setup_logger():
    with open(os.path.join(ROOT_DIR, 'logging.yaml'), 'r') as config_file:
        log_cfg = yaml.safe_load(config_file.read())
        logging.config.dictConfig(log_cfg)
