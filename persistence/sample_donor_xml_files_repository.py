"""Module for handling sample donor persistence in XML files"""
import logging
import os
from typing import List, OrderedDict, Any, Generator

from dateutil.parser import ParserError
from glom import glom

from model.gender import Gender
from model.interface.sample_donor_interface import SampleDonorInterface
from model.sample_donor import SampleDonor
from model.miabis.sample_donor_miabis import SampleDonorMiabis
from persistence.sample_donor_repository import SampleDonorRepository
from persistence.xml_util import parse_xml_file, WrongXMLFormatError
from util.custom_logger import setup_logger
from dateutil import parser as date_parser

setup_logger()
logger = logging.getLogger()


class SampleDonorXMLFilesRepository(SampleDonorRepository):
    """Class for handling sample donors stored in XML files"""

    def __init__(self, records_path: str, donor_parsing_map: dict, miabis_on_fhir_model: bool = False):
        self._dir_path = records_path
        self._ids: set = set()
        self._donor_parsing_map = donor_parsing_map
        self._miabis_on_fhir_model = miabis_on_fhir_model
        logger.debug(f"Loaded the following donor parsing map {donor_parsing_map}")

    def get_all(self) -> Generator[SampleDonorInterface,None,None]:
        dir_entry: os.DirEntry
        for dir_entry in os.scandir(self._dir_path):
            if dir_entry.name.lower().endswith(".xml"):
                yield from self.__extract_donor_from_xml_file(dir_entry)

    def __extract_donor_from_xml_file(self, dir_entry: os.DirEntry) -> SampleDonorInterface:
        """Extracts SampleDonor from an XML file"""
        donor = None
        try:
            contents = parse_xml_file(dir_entry)
            donor = self.__build_donor(contents)
        except ParserError as err:
            logger.warning(err)
        except WrongXMLFormatError:
            logger.warning(f"Wrong format of xml file, please make sure the file {dir_entry} is correct")
            return
        except TypeError as err:
            logger.warning(err)
        except ValueError as err:
            logger.warning(err)
        if donor is not None and donor.identifier not in self._ids:
            self._ids.add(donor.identifier)
            yield donor

    def __build_donor(self, data: OrderedDict[str, Any]) -> SampleDonorInterface:
        """Build sample donor object based on MIABIS on FHIR specification"""
        identifier = glom(data, self._donor_parsing_map.get("id"))
        # TODO what if gender if just an abbrevation?
        gender = Gender[(glom(data, self._donor_parsing_map.get("gender"))).upper()]
        birth_date = glom(data, self._donor_parsing_map.get("birthDate"), default=None)
        if birth_date is not None:
            try:
                birth_date = date_parser.parse(birth_date)
            except ParserError:
                raise ParserError(
                    f"Error parsing birthdate with value {birth_date} for donor with identifier: {identifier}")
        if self._miabis_on_fhir_model:
            donor = SampleDonorMiabis(identifier=identifier, gender=gender, birth_date=birth_date)
        else:
            donor = SampleDonor(identifier=identifier, gender=gender, birth_date=birth_date)
        return donor
