"""Module containing classes tied to condition persistence in XML files"""
import logging
import os
from typing import List

from glom import glom

from model.condition import Condition
from persistence.condition_repository import ConditionRepository
from persistence.xml_util import parse_xml_file, WrongXMLFormatError
from util.custom_logger import setup_logger

setup_logger()
logger = logging.getLogger()


class ConditionXMLRepository(ConditionRepository):
    """Class for handling condition persistence in XML files"""

    def __init__(self, records_path: str, condition_parsing_map: dict):
        self._dir_path = records_path
        self._sample_parsing_map = condition_parsing_map
        logger.debug(f"Loaded the following condition parsing map {condition_parsing_map}")

    def get_all(self) -> List[Condition]:
        dir_entry: os.DirEntry
        for dir_entry in os.scandir(self._dir_path):
            if dir_entry.name.lower().endswith(".xml"):
                yield from self.__extract_condition_from_xml_file(dir_entry)

    def __extract_condition_from_xml_file(self, dir_entry: os.DirEntry) -> Condition:
        """Extracts Condition from an XML file"""
        file_content = parse_xml_file(dir_entry)
        try:
            for diagnosis in glom(file_content, self._sample_parsing_map.get("icd-10_code")):
                try:
                    condition = Condition(patient_id=glom(file_content, self._sample_parsing_map.get("patient_id")),
                                          icd_10_code=diagnosis)
                    yield condition
                except TypeError:
                    logger.info("Parsed string is not a valid ICD-10 code. Skipping...")
                    return
        except WrongXMLFormatError:
            return
