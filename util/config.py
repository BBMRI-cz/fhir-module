"""Module containing application configuration variables"""
import os

BLAZE_URL = os.getenv("BLAZE_URL", "http://localhost:8080/fhir")
