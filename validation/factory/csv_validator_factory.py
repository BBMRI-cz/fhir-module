from util.config import get_parsing_map, get_records_dir_path, get_csv_separator
from validation.csv_validator import CsvValidator
from validation.validator import Validator
from validation.factory.validator_factory import ValidatorFactory


class CsvValidatorFactory(ValidatorFactory):
    def create_validator(self) -> Validator:
        return CsvValidator(get_parsing_map(), get_records_dir_path(), get_csv_separator())
