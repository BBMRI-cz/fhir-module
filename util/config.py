"""Module containing application configuration variables"""
import json
import os

BLAZE_URL = os.getenv("BLAZE_URL", "http://localhost:8080/fhir")
RECORDS_DIR_PATH = os.getenv("DIR_PATH", "/mock_dir/")
with open("/Users/radovan.tomasik/Repositories/fhir-module/util/default_map.json") as json_file:
    PARSING_MAP = json.load(json_file)
