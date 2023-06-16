import logging

import yaml
import logging.config


def setup_logger():
    with open('util/logging.yaml', 'r') as f:
        log_cfg = yaml.safe_load(f.read())
        logging.config.dictConfig(log_cfg)
