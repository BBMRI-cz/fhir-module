from exception.wrong_records_file_type_exception import WrongRecordsFileTypeException
from util.config import get_records_file_type
from validation.factory.validator_factory import ValidatorFactory
from validation.factory.csv_validator_factory import CsvValidatorFactory
from validation.factory.xml_validator_factory import XMLValidatorFactory


def get_validator_factory() -> ValidatorFactory:
    match get_records_file_type().lower():
        case "csv":
            return CsvValidatorFactory()
        case "xml":
            return XMLValidatorFactory()
        case _:
            raise WrongRecordsFileTypeException("RECORDS_FILE_TYPE environment variable has unsupported file type.")