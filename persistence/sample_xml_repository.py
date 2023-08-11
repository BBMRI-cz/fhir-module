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

    def __init__(self, records_path: str, sample_parsing_map: dict):
        self._dir_path = records_path
        self._sample_parsing_map = sample_parsing_map
        logger.debug(f"Loaded the following sample parsing map {sample_parsing_map}")

    def get_all(self) -> List[Sample]:
        for dir_entry in os.scandir(self._dir_path):
            yield from self.__extract_sample_from_xml_file(dir_entry)

    def __extract_sample_from_xml_file(self, dir_entry: os.DirEntry) -> Sample:
        """Extracts Sample from an XML file"""
        file_content = parse_xml_file(dir_entry)
        try:
            for xml_sample_id in glom(file_content, self._sample_parsing_map.get("id")):
                logger.debug(f"Found a specimen with ID: {xml_sample_id}")
                sample = Sample(xml_sample_id, file_content.get("patient", {}).get("@id", {}))
                yield sample
        except WrongXMLFormatError:
            logger.warning("Error reading XML file.")
            return
