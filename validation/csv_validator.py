import csv
import logging
import os
import sys

from exception.no_files_provided import NoFilesProvidedException
from exception.nonexistent_attribute_parsing_map import NonexistentAttributeParsingMapException
from exception.wrong_parsing_map import WrongParsingMapException
from util.custom_logger import setup_logger
from validation.validator import Validator

setup_logger()
logger = logging.getLogger()


class CsvValidator(Validator):
    """Concrete implementation of Validator abstract class. Handles the validation of CSV files"""

    def __init__(self, parsing_map: dict, records_path: str, separator: str):
        super().__init__(parsing_map, records_path)
        self._separator = separator

    def _validate_files_present(self, file_type: str) -> bool:
        """this method validates if files with correct format are provided inside the specified directory. """
        for dir_entry in os.scandir(self._dir_path):
            if dir_entry.name.endswith("." + file_type):
                return True
        logger.error("No CSV files are provided for data transformation. "
                     "Please check that you provided correct directory in DIR_PATH variable.")
        raise NoFilesProvidedException

    def _validate_single_file(self, file: os.DirEntry) -> bool:
        """Validates if the fields in header of the csv file
        correspond to the name/value pairs provided in parsing map"""
        with open(file, "r") as file_content:
            reader = csv.reader(file_content, delimiter=self._separator)
            fields = next(reader)
            return self._validate_file_attributes(fields, self._get_properties())

    def _get_properties(self) -> list[str]:
        """method that extracts all the necessary attributes  in the form of name of the properties of this class."""
        return [attr for attr in dir(self) if attr.startswith(("_donor", "_sample", "_condition"))]

    def _validate_file_attributes(self, fields: list[str], properties: list[str]) -> bool:
        """Validates that all the values defined by parsing_map are present in the header of the csv file."""
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
        return self._validate_files_structure("csv")
