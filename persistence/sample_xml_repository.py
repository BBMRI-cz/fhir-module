import logging
import os
from typing import List

from glom import glom

from model.sample import Sample
from persistence.sample_repository import SampleRepository
from persistence.xml_util import parse_xml_file, WrongXMLFormatError
from util.custom_logger import setup_logger

setup_logger()
logger = logging.getLogger()


class SampleXMLRepository(SampleRepository):
    """Class for handling sample persistence in XML files."""

    def __init__(self, dir_path: str):
        self._dir_path = dir_path

    def get_all(self) -> List[Sample]:
        for dir_entry in os.scandir(self._dir_path):
            yield from self.__extract_sample_from_xml_file(dir_entry)

    def __extract_sample_from_xml_file(self, dir_entry: os.DirEntry) -> Sample:
        """Extracts Sample from an XML file"""
        file_content = parse_xml_file(dir_entry)
        try:
            for xml_sample in glom(file_content, '**.STS.[]'):
                yield Sample(xml_sample.get("@sampleId", {}), file_content.get("patient", {}).get("@id", {}))
        except WrongXMLFormatError:
            return
