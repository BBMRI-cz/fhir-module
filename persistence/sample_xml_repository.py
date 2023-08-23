import logging
import os
from typing import Generator

from glom import glom, PathAccessError

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

    def get_all(self) -> Generator[Sample, None, None]:
        for dir_entry in os.scandir(self._dir_path):
            yield from self.__extract_sample_from_xml_file(dir_entry)

    def __extract_sample_from_xml_file(self, dir_entry: os.DirEntry) -> Sample:
        """Extracts Sample from an XML file"""
        file_content = parse_xml_file(dir_entry)
        for parsing_path in str(self._sample_parsing_map.get("sample")).split(" || "):
            try:
                for xml_sample in flatten_list(glom(file_content, parsing_path)):
                    logger.debug(f"Found a specimen: {xml_sample}")
                    yield self.__build_sample(file_content, xml_sample)
            except (WrongXMLFormatError, PathAccessError, TypeError):
                logger.warning("Error reading XML file.")
                return

    def __build_sample(self, file_content, xml_sample):
        return Sample(identifier=glom(xml_sample,
                                      self._sample_parsing_map.get("sample_details").get("id")),
                      donor_id=glom(file_content,
                                    self._sample_parsing_map.get("donor_id")),
                      material_type=glom(xml_sample,
                                         self._sample_parsing_map.get("sample_details").get(
                                             "material_type"),
                                         default=None),
                      diagnosis=glom(xml_sample,
                                     self._sample_parsing_map.get("sample_details").get(
                                         "diagnosis"), default=None))


def flatten_list(nested_list):
    return [item for sublist in nested_list for item in
            (flatten_list(sublist) if isinstance(sublist, list) else [sublist])]
