"""Module containing classes tied to condition persistence in XML files"""
import os
from typing import List

from glom import glom

from model.condition import Condition
from persistence.condition_repository import ConditionRepository
from persistence.xml_util import parse_xml_file, WrongXMLFormatError


class ConditionXMLRepository(ConditionRepository):
    """Class for handling condition persistence in XML files"""

    def __init__(self):
        self._dir_path = os.getenv("DIR_PATH", "/mock_dir/")

    def get_all(self) -> List[Condition]:
        for dir_entry in os.scandir(self._dir_path):
            yield from self.__extract_condition_from_xml_file(dir_entry)

    def __extract_condition_from_xml_file(self, dir_entry: os.DirEntry) -> Condition:
        """Extracts Condition from an XML file"""
        file_content = parse_xml_file(dir_entry)
        try:
            for diagnosis in glom(file_content, '**.diagnosis'):
                condition = Condition(patient_id=glom(file_content, 'patient.@id'),
                                      icd_10_code=diagnosis)
                yield condition
        except WrongXMLFormatError:
            return
