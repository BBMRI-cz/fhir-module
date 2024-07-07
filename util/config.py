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
PARSING_MAP_CSV_PATH = os.getenv("PARSING_MAP_PATH", os.path.join(ROOT_DIR, 'default_csv_map.json'))
MATERIAL_TYPE_MAP_PATH = os.getenv("MATERIAL_TYPE_MAP_PATH", os.path.join(ROOT_DIR, 'default_material_type_map.json'))
SAMPLE_COLLECTIONS_PATH = os.getenv("SAMPLE_COLLECTIONS_PATH", os.path.join(ROOT_DIR, 'default_sample_collection.json'))
TYPE_TO_COLLECTION_MAP_PATH = os.getenv("TYPE_TO_COLLECTION_MAP_PATH",
                                        os.path.join(ROOT_DIR, 'default_type_to_collection_map.json'))
STORAGE_TEMP_MAP_PATH = os.getenv("STORAGE_TEMP_MAP_PATH", os.path.join(ROOT_DIR, 'default_storage_temp_map.json'))

COLLECTION_MAPPING_ATTRIBUTE = os.getenv("COLLECTION_MAPPING_ATTRIBUTE", "material_type")
CSV_SEPARATOR = os.getenv("CSV_SEPARATOR", ";")
RECORDS_FILE_TYPE = os.getenv("RECORDS_FILE_TYPE", "xml")
BLAZE_AUTH: tuple = (os.getenv("BLAZE_USER", ""), os.getenv("BLAZE_PASS", ""))
with open(PARSING_MAP_PATH) as json_file:
    try:
        PARSING_MAP = json.load(json_file)
    except JSONDecodeError:
        logger.error("Parsing map does not have correct JSON format. Exiting.")
        sys.exit()

with open(PARSING_MAP_CSV_PATH) as json_file:
    try:
        PARSING_MAP_CSV = json.load(json_file)
    except JSONDecodeError:
        logger.error("Parsing map does not have correct JSON format. Exiting.")
        sys.exit()

with open(MATERIAL_TYPE_MAP_PATH) as json_file:
    try:
        MATERIAL_TYPE_MAP = json.load(json_file)
    except JSONDecodeError:
        logger.error("Material type map does not have correct JSON format. Exiting.")
        sys.exit()

with open(TYPE_TO_COLLECTION_MAP_PATH) as json_file:
    try:
        TYPE_TO_COLLECTION_MAP = json.load(json_file)
    except JSONDecodeError:
        logger.error("Type to collection map does not have correct JSON format. Exiting.")
        sys.exit()

with open(STORAGE_TEMP_MAP_PATH) as json_file:
    try:
        STORAGE_TEMP_MAP = json.load(json_file)
    except JSONDecodeError:
        logger.error("Storage temperature map does not have correct JSON format. Exiting.")
        sys.exit()
