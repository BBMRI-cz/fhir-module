"""Module containing application configuration variables"""
import os

BLAZE_URL = os.getenv("BLAZE_URL", "http://localhost:8080/fhir")
RECORDS_DIR_PATH = os.getenv("DIR_PATH", "/mock_dir/")
