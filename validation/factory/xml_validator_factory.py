from util.config import PARSING_MAP, RECORDS_DIR_PATH
from validation.factory.validator_factory import ValidatorFactory
from validation.validator import Validator
from validation.xml_validator import XMLValidator


class XMLValidatorFactory(ValidatorFactory):
    def create_validator(self) -> Validator:
        return XMLValidator(PARSING_MAP, RECORDS_DIR_PATH)
