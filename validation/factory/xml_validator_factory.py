from util.config import get_parsing_map, get_records_dir_path
from validation.factory.validator_factory import ValidatorFactory
from validation.validator import Validator
from validation.xml_validator import XMLValidator


class XMLValidatorFactory(ValidatorFactory):
    def create_validator(self) -> Validator:
        return XMLValidator(get_parsing_map(), get_records_dir_path())
