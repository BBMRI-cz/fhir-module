import logging
import os
import sys

from glom import glom, PathAccessError

from exception.no_files_provided import NoFilesProvidedException
from exception.nonexistent_attribute_parsing_map import NonexistentAttributeParsingMapException
from exception.wrong_parsing_map import WrongParsingMapException
from persistence.xml_util import parse_xml_file
from util.custom_logger import setup_logger
from validation.validator import Validator

setup_logger()
logger = logging.getLogger()


class XMLValidator(Validator):
    """Concrete implementation of Validator abstract class. Handles the validation of XML files"""

    def __init__(self, parsing_map: dict, records_dir: str):
        super().__init__(parsing_map, records_dir)
        self._sample = None

    def _validate_files_present(self, file_type: str) -> bool:
        """this method validates if files with correct format are provided inside the specified directory. """
        dir_entry: os.DirEntry
        for dir_entry in os.scandir(self._dir_path):
            if dir_entry.name.lower().endswith("." + file_type):
                return True
        logger.error("No XML files are provided for data transformation. "
                     "Please check that you provided correct directory in DIR_PATH variable.")
        raise NoFilesProvidedException

    def _validate_single_file(self, file: os.DirEntry) -> bool:
        """Validates presence of xml tags which names are specified in the provided parsing_map"""
        file_content = parse_xml_file(file)
        donor_and_condition_properties = [attr for attr in dir(self) if
                                          attr.startswith(("_donor", "_condition"))]

        return self._validate_file_attributes(file_content,
                                              donor_and_condition_properties) and self._validate_sample_attributes(
            file_content)

    def _validate_sample_attributes(self, file_content: dict) -> bool:
        for parsing_path in str(self._sample).split(" || "):
            try:
                for xml_sample in self.flatten_list(glom(file_content, parsing_path)):
                    glom(xml_sample, self._sample_id)
                    glom(xml_sample, self._sample_diagnosis)
                    glom(xml_sample, self._sample_material_type)
                    # Break because we only need to test one sample
                    break
            except PathAccessError:
                logger.error(f"Provided parsing map contains the necessary name/value pairs, however,"
                             f" values from sample_map dont have corresponding values in the xml file.")
                raise NonexistentAttributeParsingMapException
            return True

    def _validate_file_attributes(self, file_content: dict, properties: list[str]):
        """Validates that all the values defined by parsing_map are present as a xml tags."""
        for prop in properties:
            prop_value = getattr(self, prop)
            try:
                glom(file_content, prop_value)
            except PathAccessError:
                logger.error(f"Provided parsing map contains the necessary name/value pairs, however, name \"{prop}\" "
                             f"does not have the corresponding pair "
                             f"(which based on parsing map should be \"{prop_value}\")")
                raise NonexistentAttributeParsingMapException
        return True

    def _validate_sample_map(self) -> bool:
        super()._validate_sample_map()
        self._sample = self._map_sample.get("sample")
        if self._sample is None:
            logger.error(f"Provided parsing map does not contain the necessary name/value pairs for sample map."
                         f"sample_map needs to contain the following names(attributes): \"sample\"")
            raise WrongParsingMapException
        return True

    def flatten_list(self, nested_list):
        return [item for sublist in nested_list for item in
                (self.flatten_list(sublist) if isinstance(sublist, list) else [sublist])]

    def validate(self) -> bool:
        super()._validate_donor_map()
        self._validate_sample_map()
        super()._validate_condition_map()

        return self._validate_files_structure("xml")
