import csv
import logging
import os

from util.custom_logger import setup_logger
from validator import Validator
from exception.nonexistent_attribute_parsing_map import NonexistentAttributeParsingMapException

setup_logger()
logger = logging.getLogger()


class CsvValidator(Validator):

    def __init__(self, parsing_map: dict, records_path: str, separator: str):
        super().__init__(parsing_map, records_path)
        self._separator = separator

    def _validate_files_structure(self) -> bool:
        """This method validates, if all the files meant for data transformation have the necessary structure"""
        dir_entry: os.DirEntry
        for dir_entry in os.scandir(self._dir_path):
            if dir_entry.name.endswith(".csv"):
                self._validate_single_file(dir_entry)
        return True

    def _validate_single_file(self, csv_file: os.DirEntry) -> bool:
        """Validates if the fields in header of the csv file
        correspond to the name/value pairs provided in parsing map"""
        with open(csv_file, "r") as file_content:
            reader = csv.reader(file_content, delimiter=self._separator)
            fields = next(reader)
            return self._validate_file_attributes(fields, self._get_properties())

    def _validate_file_attributes(self, fields: list[str], properties: list[str]) -> bool:
        for prop in properties:
            prop_value = getattr(self, prop)
            if prop_value not in fields:
                logger.error(f"Provided parsing map contains the necessary name/value pairs, however, name \"{prop}\" "
                             f"does not have the corresponding pair "
                             f"(which based on parsing map should be \"{prop_value}\")")
                raise NonexistentAttributeParsingMapException
            return True

    def validate(self) -> bool:
        super()._validate_donor_map()
        super()._validate_sample_map()
        super()._validate_condition_map()
        return self._validate_files_structure()
