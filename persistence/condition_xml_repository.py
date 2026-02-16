"""Module containing classes tied to condition persistence in XML files"""
import logging
import os
from typing import List

from dateutil import parser as date_parser
from dateutil.parser import ParserError
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
        try:
            file_content = parse_xml_file(dir_entry)
        except WrongXMLFormatError:
            logger.info(f"Wrong XLM format of file: {dir_entry.name} [Skipping...]")
            return
        try:
            for diagnosis in glom(file_content, self._sample_parsing_map.get("icd-10_code")):
                patient_id = glom(file_content, self._sample_parsing_map.get("patient_id"))
                try:
                    diagnosis_datetime = glom(file_content, self._sample_parsing_map.get("diagnosis_date"),
                                              default=None)

                    if len(diagnosis_datetime) == 0:
                        diagnosis_datetime = None
                    if diagnosis_datetime is not None:
                        try:
                            diagnosis_datetime = date_parser.parse(diagnosis_datetime[0])
                            diagnosis_datetime = diagnosis_datetime.replace(hour=0, minute=0, second=0)
                        except ParserError:
                            logger.info(
                                f"Error parsing date for condition for patient with id {patient_id} "
                                f"while parsing diagnosis datetime with value {diagnosis}. "
                                f"Please make sure the date is in a valid format."
                                f"Skipping ...")
                            return
                    condition = Condition(patient_id=patient_id,
                                          icd_10_code=diagnosis,
                                          diagnosis_datetime=diagnosis_datetime)
                    yield condition
                except TypeError:
                    logger.info("Parsed string is not a valid ICD-10 code. Skipping...")
                    return
        except WrongXMLFormatError:
            return
