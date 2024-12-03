import logging
import os
import time

from util.custom_logger import setup_logger

setup_logger()
logger = logging.getLogger()


def get_file_age(file_path: str):
    modification_time = os.path.getmtime(file_path)
    file_age_seconds = time.time() - modification_time
    file_age_days = file_age_seconds / (60 * 60 * 24)
    return file_age_days