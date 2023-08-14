"""Module containing application configuration variables"""
import json
import logging
import os
import sys
from json import JSONDecodeError

from util.custom_logger import setup_logger

setup_logger()
logger = logging.getLogger()

BLAZE_URL = os.getenv("BLAZE_URL", "http://localhost:8080/fhir")
RECORDS_DIR_PATH = os.getenv("DIR_PATH", "/mock_dir/")
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PARSING_MAP_PATH = os.getenv("PARSING_MAP_PATH", os.path.join(ROOT_DIR, 'default_map.json'))
with open(PARSING_MAP_PATH) as json_file:
    try:
        PARSING_MAP = json.load(json_file)
    except JSONDecodeError:
        logger.error("Parsing map does not have correct JSON format. Exiting.")
        sys.exit()
