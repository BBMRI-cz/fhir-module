import logging
import os

from exception.nonexistent_attribute_parsing_map import NonexistentAttributeParsingMapException
from exception.wrong_parsing_map import WrongParsingMapException
from persistence.xml_util import parse_xml_file
from util.custom_logger import setup_logger
from validator import Validator

setup_logger()
logger = logging.getLogger()


class XMLValidator(Validator):
    def __init__(self, parsing_map: dict, records_dir: str):
        super().__init__(parsing_map, records_dir)
        self._sample = None

    def _validate_file_structure(self) -> bool:
        dir_entry: os.DirEntry
        for dir_entry in os.scandir(self._dir_path):
            if dir_entry.name.endswith(".xml"):
                self._validate_single_file(dir_entry)
        return True

    def _validate_single_file(self, xml_file: os.DirEntry) -> bool:
        file_content = parse_xml_file(xml_file)
        return self._validate_file_attributes(file_content, self._get_properties())

    def _validate_file_attributes(self, file_content: dict, properties: list[str]):
        for prop in properties:
            prop_value = getattr(self, prop)
            if prop_value not in file_content:
                logger.error(f"Provided parsing map contains the necessary name/value pairs, however, name \"{prop}\" "
                             f"does not have the corresponding pair "
                             f"(which based on parsing map should be \"{prop_value}\")")
                raise NonexistentAttributeParsingMapException
            return True

    def _validate_sample_map(self) -> bool:
        super()._validate_sample_map()
        self._sample = self._map_sample["sample"]
        if self._sample is None:
            logger.error(f"Provided parsing map does not contain the necessary name/value pairs for sample map."
                         f"sample_map needs to contain the following names(attributes): \"sample\"")
            raise WrongParsingMapException
        return True

    def validate(self) -> bool:
        super()._validate_donor_map()
        self._validate_sample_map()
        super()._validate_condition_map()
