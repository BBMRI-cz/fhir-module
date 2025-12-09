"""Module for handling sample donor persistence in XML files"""
import logging
import os
from typing import Callable, OrderedDict, Any, Generator

from dateutil import parser as date_parser
from dateutil.parser import ParserError
from glom import glom
from miabis_model import Gender as MiabisGender

from model.gender import Gender as ModuleGender
from model.interface.sample_donor_interface import SampleDonorInterface
from model.miabis.sample_donor_miabis import SampleDonorMiabis
from model.sample_donor import SampleDonor
from persistence.sample_donor_repository import SampleDonorRepository
from persistence.xml_util import parse_xml_file, WrongXMLFormatError
from util.custom_logger import setup_logger
from util.enums_util import get_gender_from_abbreviation

setup_logger()
logger = logging.getLogger()


class SampleDonorXMLFilesRepository(SampleDonorRepository):
    """Class for handling sample donors stored in XML files"""

    def __init__(self, records_path: str, donor_parsing_map: dict, miabis_on_fhir_model: bool = False):
        super().__init__(records_path)
        self._ids: set = set()
        self._donor_parsing_map = donor_parsing_map
        self._miabis_on_fhir_model = miabis_on_fhir_model
        logger.debug(f"Loaded the following donor parsing map {donor_parsing_map}")

    def get_all(self) -> Generator[SampleDonorInterface, None, None]:
        self._ids = set()
        with os.scandir(self._dir_path) as entries:
            for dir_entry in entries:
                if dir_entry.name.lower().endswith(".xml"):
                    yield from self.__extract_donor_from_xml_file(dir_entry)

    def update_mappings(self) -> None:
        super().update_mappings()

    def _get_supported_extensions(self) -> tuple[str, Callable]:
        return ".xml", self.__validate_donor_from_xml_file

    def __extract_donor_from_xml_file(self, dir_entry: os.DirEntry) -> SampleDonorInterface:
        """Extracts SampleDonor from an XML file"""
        donor = None
        try:
            contents = parse_xml_file(dir_entry)
            donor = self.__build_donor(contents)
        except ParserError as err:
            logger.warning(err)
        except WrongXMLFormatError:
            logger.info(f"Wrong XLM format of file: {dir_entry.name} [Skipping...]")
            return
        except (ValueError, TypeError, KeyError) as err:
            logger.warning(err)
        if donor is not None and donor.identifier not in self._ids:
            self._ids.add(donor.identifier)
            yield donor

    def __validate_donor_from_xml_file(self, dir_entry: os.DirEntry) -> list[str]:
        errors = []
        donor = None
        try:
            contents = parse_xml_file(dir_entry)
            donor = self.__build_donor(contents, is_validation=True)
        except ExceptionGroup as eg:
            for exc in eg.exceptions:
                errors.append(f"File {dir_entry.name} - Sample Donor: {exc}")
            return errors
        except WrongXMLFormatError:
            errors.append(f"File {dir_entry.name} - Wrong XML format [Skipping...]")
            return errors
        except (ValueError, TypeError, KeyError) as err:
            errors.append(f"File {dir_entry.name} - Sample Donor: {err}")
        if donor is not None and donor.identifier not in self._ids:
            self._ids.add(donor.identifier)
        return errors
    
    def __parse_xml_gender(self, data: OrderedDict[str, Any]):
        """Parse and validate the gender field from XML."""
        gender_string = (glom(data, self._donor_parsing_map.get("gender"))).upper()
        
        # If it's a single character, treat it as an abbreviation
        if len(gender_string) == 1:
            return get_gender_from_abbreviation(gender_string)
        
        # Otherwise, try to parse it as a full gender name
        try:
            if self._miabis_on_fhir_model:
                return MiabisGender[gender_string]
            else:
                return ModuleGender[gender_string]
        except ValueError:
            if self._miabis_on_fhir_model:
                return MiabisGender.UNKNOWN
            else:
                return ModuleGender.UNKNOWN

    def __parse_xml_birth_date(self, data: OrderedDict[str, Any], identifier: str, 
                                validation_errors: list | None):
        """Parse the optional birth date field from XML."""
        birth_date_path = self._donor_parsing_map.get("birthDate")
        if birth_date_path is None:
            return None
        
        birth_date = glom(data, birth_date_path, default=None)
        if birth_date is None:
            return None
        
        try:
            return date_parser.parse(birth_date)
        except ParserError:
            exception = ParserError(
                f"Sample Donor: Error parsing birthdate with value {birth_date} "
                f"for donor with identifier: {identifier}"
            )
            if validation_errors is not None:
                validation_errors.append(exception)
            else:
                raise exception

    def __create_xml_donor_object(self, identifier: str, gender, birth_date) -> SampleDonorInterface:
        """Create the appropriate SampleDonor or SampleDonorMiabis object."""
        if self._miabis_on_fhir_model:
            return SampleDonorMiabis(identifier=identifier, gender=gender, birth_date=birth_date)
        else:
            return SampleDonor(identifier=identifier, gender=gender, birth_date=birth_date)

    def __build_donor(self, data: OrderedDict[str, Any], is_validation: bool = False) -> SampleDonorInterface:
        """Build sample donor object based on MIABIS on FHIR specification"""
        validation_errors = [] if is_validation else None
        
        # Extract mandatory identifier
        identifier = glom(data, self._donor_parsing_map.get("id"))
        
        # Parse gender (mandatory)
        gender = self.__parse_xml_gender(data)
        
        # Parse optional birth date
        birth_date = self.__parse_xml_birth_date(data, identifier, validation_errors)
        
        # If in validation mode and there are errors, raise them all together
        if is_validation and validation_errors:
            raise ExceptionGroup("Validation errors", validation_errors)
        
        # Create and return the appropriate donor object
        return self.__create_xml_donor_object(identifier, gender, birth_date)
