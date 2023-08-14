"""Module for handling sample donor persistence in XML files"""
import logging
import os
from typing import List

from glom import glom

from model.gender import Gender
from model.sample_donor import SampleDonor
from persistence.sample_donor_repository import SampleDonorRepository
from persistence.xml_util import parse_xml_file, WrongXMLFormatError
from util.custom_logger import setup_logger

setup_logger()
logger = logging.getLogger()


class SampleDonorXMLFilesRepository(SampleDonorRepository):
    """Class for handling sample donors stored in XML files"""

    def __init__(self, records_path: str, donor_parsing_map: dict):
        self._dir_path = records_path
        self._ids: set = set()
        self._donor_parsing_map = donor_parsing_map
        logger.debug(f"Loaded the following donor parsing map {donor_parsing_map}")

    def get_all(self) -> List[SampleDonor]:
        for dir_entry in os.scandir(self._dir_path):
            yield from self.__extract_donor_from_xml_file(dir_entry)

    def __extract_donor_from_xml_file(self, dir_entry: os.DirEntry) -> SampleDonor:
        """Extracts SampleDonor from an XML file"""
        try:
            contents = parse_xml_file(dir_entry)
            donor = SampleDonor(glom(contents, self._donor_parsing_map.get("id")))
            donor.gender = Gender[(glom(contents, self._donor_parsing_map.get("gender"))).upper()]
        except WrongXMLFormatError:
            return
        if donor.identifier not in self._ids:
            self._ids.add(donor.identifier)
            yield donor
