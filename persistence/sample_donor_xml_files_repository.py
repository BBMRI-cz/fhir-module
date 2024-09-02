"""Module for handling sample donor persistence in XML files"""
import logging
import os
from datetime import datetime
from typing import List

from dateutil.parser import ParserError
from glom import glom

from model.gender import Gender
from model.sample_donor import SampleDonor
from persistence.sample_donor_repository import SampleDonorRepository
from persistence.xml_util import parse_xml_file, WrongXMLFormatError
from util.custom_logger import setup_logger
from util.date_util import parse_date
from dateutil import parser as date_parser

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
        dir_entry: os.DirEntry
        for dir_entry in os.scandir(self._dir_path):
            if dir_entry.name.lower().endswith(".xml"):
                yield from self.__extract_donor_from_xml_file(dir_entry)

    def __extract_donor_from_xml_file(self, dir_entry: os.DirEntry) -> SampleDonor:
        """Extracts SampleDonor from an XML file"""
        try:
            contents = parse_xml_file(dir_entry)
            donor = SampleDonor(glom(contents, self._donor_parsing_map.get("id")))
            donor.gender = Gender[(glom(contents, self._donor_parsing_map.get("gender"))).upper()]
            year_of_birth = glom(contents, self._donor_parsing_map.get("birthDate"), default=None)
            if year_of_birth is not None:
                donor.date_of_birth = date_parser.parse(year_of_birth)
                # donor.date_of_birth = parse_date(year_of_birth)
        except ParserError:
            logger.warning(
                f"Error parsing date. Please make sure the date is in a valid format.")
        except WrongXMLFormatError:
            return
        if donor.identifier not in self._ids:
            self._ids.add(donor.identifier)
            yield donor
