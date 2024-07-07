import logging
import os
from typing import Generator

from dateutil.parser import ParserError
from glom import glom, PathAccessError

from model.sample import Sample
from persistence.sample_repository import SampleRepository
from persistence.xml_util import parse_xml_file, WrongXMLFormatError
from util.custom_logger import setup_logger
from util.enums_util import parse_storage_temp_from_code
from dateutil import parser as date_parser

setup_logger()
logger = logging.getLogger()


class SampleXMLRepository(SampleRepository):
    """Class for handling sample persistence in XML files."""

    def __init__(self, records_path: str, sample_parsing_map: dict, type_to_collection_map: dict = None,
                 storage_temp_map: dict = None, attribute_to_collection: str = None):
        self._dir_path = records_path
        self._sample_parsing_map = sample_parsing_map
        logger.debug(f"Loaded the following sample parsing map {sample_parsing_map}")
        self._type_to_collection_map = type_to_collection_map
        self._storage_temp_map = storage_temp_map
        self._attribute_to_collection = attribute_to_collection

    def get_all(self) -> Generator[Sample, None, None]:
        dir_entry: os.DirEntry
        for dir_entry in os.scandir(self._dir_path):
            if dir_entry.name.lower().endswith(".xml"):
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
        sample = Sample(identifier=glom(xml_sample,
                                        self._sample_parsing_map.get("sample_details").get("id")),
                        donor_id=glom(file_content,
                                      self._sample_parsing_map.get("donor_id")),
                        material_type=glom(xml_sample,
                                           self._sample_parsing_map.get("sample_details").get(
                                               "material_type"),
                                           default=None),
                        )
        diagnoses = glom(xml_sample,
                         self._sample_parsing_map.get("sample_details").get(
                             "diagnosis"), default=None)
        if diagnoses is not None:
            sample.diagnoses = [diagnoses] if isinstance(diagnoses, str) else diagnoses

        collection_date = glom(xml_sample, self._sample_parsing_map.get("sample_details").get("collection_date"),
                               default=None)
        if collection_date is not None:
            try:
                sample.collected_datetime = date_parser.parse(collection_date).date()
            except ParserError:
                logger.warning(f"Error parsing date {collection_date}. Please make sure the date is in a valid format.")
                pass
        if self._type_to_collection_map is not None and self._attribute_to_collection is not None:
            collection_id = glom(xml_sample, self._sample_parsing_map.get(self._attribute_to_collection),
                                 default=None)
            sample.sample_collection_id = collection_id
        if self._storage_temp_map is not None:
            storage_temp_code = glom(xml_sample,
                                     self._sample_parsing_map.get("sample_details").get("storage_temperature"),
                                     default=None)
            if storage_temp_code is not None:
                sample.storage_temperature = parse_storage_temp_from_code(self._storage_temp_map, storage_temp_code)
        return sample


def flatten_list(nested_list):
    return [item for sublist in nested_list for item in
            (flatten_list(sublist) if isinstance(sublist, list) else [sublist])]
