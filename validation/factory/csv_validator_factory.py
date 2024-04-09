from util.config import PARSING_MAP, RECORDS_DIR_PATH, CSV_SEPARATOR
from validation.csv_validator import CsvValidator
from validation.validator import Validator
from validation.factory.validator_factory import ValidatorFactory


class CsvValidatorFactory(ValidatorFactory):
    def create_validator(self) -> Validator:
        return CsvValidator(PARSING_MAP, RECORDS_DIR_PATH, CSV_SEPARATOR)
