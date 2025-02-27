"""Module containing application configuration variables"""
import json
import logging
import os
import sys
from json import JSONDecodeError
from distutils.util import strtobool

from util.custom_logger import setup_logger

setup_logger()
logger = logging.getLogger()

BLAZE_URL = os.getenv("BLAZE_URL", "http://localhost:8080/fhir")
MIABIS_BLAZE_URL = os.getenv("MIABIS_BLAZE_URL", "http://localhost:5432/fhir")
RECORDS_DIR_PATH = os.getenv("DIR_PATH", "/mock_dir/")
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

PARSING_MAP_PATH = os.getenv("PARSING_MAP_PATH", os.path.join(ROOT_DIR, 'default_map.json'))
PARSING_MAP_CSV_PATH = os.getenv("PARSING_MAP_PATH", os.path.join(ROOT_DIR, 'default_csv_map.json'))
MATERIAL_TYPE_MAP_PATH = os.getenv("MATERIAL_TYPE_MAP_PATH", os.path.join(ROOT_DIR, 'default_material_type_map.json'))
MIABIS_MATERIAL_TYPE_MAP_PATH = os.getenv("MIABIS_MATERIAL_TYPE_MAP_PATH",
                                          os.path.join(ROOT_DIR, 'default_miabis_material_type_map.json'))

SAMPLE_COLLECTIONS_PATH = os.getenv("SAMPLE_COLLECTIONS_PATH", os.path.join(ROOT_DIR, 'default_sample_collection.json'))
BIOBANK_PATH = os.getenv("BIOBANK_PATH", os.path.join(ROOT_DIR, 'default_biobank.json'))
TYPE_TO_COLLECTION_MAP_PATH = os.getenv("TYPE_TO_COLLECTION_MAP_PATH",
                                        os.path.join(ROOT_DIR, 'default_type_to_collection_map.json'))

STORAGE_TEMP_MAP_PATH = os.getenv("STORAGE_TEMP_MAP_PATH", os.path.join(ROOT_DIR, 'default_storage_temp_map.json'))
MIABIS_STORAGE_TEMP_MAP_PATH = os.getenv("MIABIS_STORAGE_TEMP_MAP_PATH",
                                         os.path.join(ROOT_DIR, 'default_miabis_storage_temp_map.json'))

STANDARDISED = bool(strtobool(os.getenv("STANDARDISED","False")))
MIABIS_ON_FHIR = bool(strtobool(os.getenv("MIABIS_ON_FHIR","True")))
CSV_SEPARATOR = os.getenv("CSV_SEPARATOR", ";")
RECORDS_FILE_TYPE = os.getenv("RECORDS_FILE_TYPE", "xml")
NEW_FILE_PERIOD_DAYS = os.getenv("NEW_FILE_PERIOD_DAYS", 30)
BLAZE_AUTH: tuple = (os.getenv("BLAZE_USER", ""), os.getenv("BLAZE_PASS", ""))
MIABIS_BLAZE_AUTH: tuple = (os.getenv("BLAZE_USER", ""), os.getenv("BLAZE_PASS", ""))

SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = os.getenv("SMTP_PORT", 1025)

EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "test@example.com")
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

with open(MIABIS_STORAGE_TEMP_MAP_PATH) as json_file:
    try:
        MIABIS_STORAGE_TEMP_MAP = json.load(json_file)
    except JSONDecodeError:
        logger.error("MIABIS Storage temperature map does not have correct JSON format. Exiting.")
        sys.exit()

with open(MIABIS_MATERIAL_TYPE_MAP_PATH) as json_file:
    try:
        MIABIS_MATERIAL_TYPE_MAP = json.load(json_file)
    except JSONDecodeError:
        logger.error("MIABIS Material type map does not have correct JSON format. Exiting.")
        sys.exit()
