import logging

from util.custom_logger import setup_logger
from validator import Validator

setup_logger()
logger = logging.getLogger()


class CsvValidator(Validator):
    def __init__(self, attributes_map: dict):
        self._attributes_map = attributes_map

    def validate(self) -> bool:
        pass
