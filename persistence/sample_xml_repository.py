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

    def __init__(self):
        self._dir_path = os.getenv("DIR_PATH", "/mock_dir/")

    def get_all(self) -> List[Sample]:
        for dir_entry in os.scandir(self._dir_path):
            yield from self.__extract_sample_from_xml_file(dir_entry)

    def __extract_sample_from_xml_file(self, dir_entry: os.DirEntry) -> Sample:
        """Extracts Sample from an XML file"""
        file_content = parse_xml_file(dir_entry)
        logger.debug(file_content)
        logger.debug("Got here.")
        try:
            for xml_sample_id in glom(file_content, "**.@sampleId"):
                logger.debug(str(xml_sample_id))
                sample = Sample(xml_sample_id, file_content.get("patient", {}).get("@id", {}))
                logger.debug(sample.identifier)
                yield sample
        except WrongXMLFormatError:
            logger.warning("Error reading XML file.")
            return
