import json
import json
import logging
import os
from json import JSONDecodeError
from typing import Callable, Generator

from dateutil import parser as date_parser
from dateutil.parser import ParserError
from miabis_model import Gender as MiabisGender
from miabis_model.gender import get_gender_from_abbreviation as miabis_get_gender_from_abbreviation

from model.gender import Gender as ModuleGender
from model.interface.sample_donor_interface import SampleDonorInterface
from model.miabis.sample_donor_miabis import SampleDonorMiabis
from model.sample_donor import SampleDonor
from persistence.sample_donor_repository import SampleDonorRepository
from util.custom_logger import setup_logger

setup_logger()
logger = logging.getLogger()


class SampleDonorJsonRepository(SampleDonorRepository):
    """Class for handling sample donors stored in Csv files"""

    def __init__(self, records_path: str, donor_parsing_map: dict, miabis_on_fhir_model: bool = False):
        super().__init__(records_path)
        self._ids: set = set()
        self._donor_parsing_map = donor_parsing_map
        self._miabis_on_fhir_model = miabis_on_fhir_model
        logger.debug(f"Loaded the following donor parsing map {donor_parsing_map}")

    def get_all(self) -> Generator[SampleDonorInterface, None, None]:
        self._ids = set()
        dir_entries = list(os.scandir(self._dir_path))
        for dir_entry in dir_entries:
            if dir_entry.name.lower().endswith(".json"):
                yield from self.__extract_donor_from_json_file(dir_entry)

    def update_mappings(self) -> None:
        """Update the mappings for the repository."""
        super().update_mappings()

    def _get_supported_extensions(self) -> tuple[str, Callable]:
        return ".json", self.__validate_donor_from_json_file

    def __extract_donor_from_json_file(self, dir_entry: os.DirEntry) -> SampleDonorInterface:
        try:
            with open(dir_entry, "r", encoding="utf-8-sig") as json_file:
                try:
                    donors_json = json.load(json_file)
                except JSONDecodeError:
                    logger.error("Biobank file does not have a correct JSON format. Exiting...")
                    return
                for donor_json in donors_json:
                    try:
                        donor = self.__build_donor(donor_json)
                        if donor.identifier not in self._ids:
                            self._ids.add(donor.identifier)
                            yield donor
                    except ParserError as err:
                        logger.info(f"{err}Skipping...")
                        continue
                    except TypeError as err:
                        logger.info(f"{err} Skipping...")
                        continue
                    except KeyError as err:
                        logger.info(f"{err} Skipping...")
                        continue
        except OSError as e:
            logger.debug(f"Error while opening file {dir_entry.name}: {e}")
            logger.info(f"Error while opening file {dir_entry.name} [Skipping...]")
            return
        
    def __validate_donor_from_json_file(self, dir_entry: os.DirEntry) -> list[str]:
        errors = []
        try:
            with open(dir_entry, "r", encoding="utf-8-sig") as json_file:
                try:
                    donors_json = json.load(json_file)
                except JSONDecodeError:
                    errors.append("Biobank file does not have a correct JSON format. Exiting...")
                    return errors
                donor_index = 0  # Start from 0 for JSON array index
                for donor_json in donors_json:
                    try:
                        donor = self.__build_donor(donor_json, is_validation=True)
                        if donor.identifier not in self._ids:
                            self._ids.add(donor.identifier)
                    except ExceptionGroup as eg:
                        for exc in eg.exceptions:
                            errors.append(f"Sample Donor (index {donor_index}): {exc}")
                    except (ValueError, TypeError, KeyError) as err:
                        errors.append(f"Sample Donor (index {donor_index}): {err}")
                    finally:
                        donor_index += 1
        except OSError as e:
            errors.append(f"Error while opening file {dir_entry.name}: {e}")
            return errors
    
        return errors
        

    def __parse_json_gender(self, data: dict, identifier: str):
        """Parse and validate the gender field from JSON."""
        gender = data.get(self._donor_parsing_map.get("gender"), None)
        if gender is None:
            raise ValueError(f"No gender provided for patient with identifier {identifier}")
        
        # If it's a single character, treat it as an abbreviation
        if len(gender) == 1:
            return miabis_get_gender_from_abbreviation(gender)
        
        # Otherwise, try to parse it as a full gender name
        try:
            if self._miabis_on_fhir_model:
                return MiabisGender[gender.upper()]
            else:
                return ModuleGender[gender.upper()]
        except (ValueError, KeyError):
            if self._miabis_on_fhir_model:
                return MiabisGender.UNKNOWN
            else:
                return ModuleGender.UNKNOWN

    def __parse_json_birth_date(self, data: dict, identifier: str, validation_errors: list):
        """Parse the optional birth date field from JSON."""
        birth_date_path = self._donor_parsing_map.get("birthDate")
        if birth_date_path is None:
            return None
        
        birth_date = data.get(birth_date_path, None)
        if birth_date is None:
            return None
        
        try:
            return date_parser.parse(birth_date)
        except ParserError:
            exception = ParserError(
                f"Error while parsing donor with identifier {identifier}. "
                f"Incorrect parsing date {birth_date}. Please make sure the date is in a valid format."
            )
            if validation_errors is not None:
                validation_errors.append(exception)
            else:
                raise exception

    def __create_json_donor_object(self, identifier: str, gender, birth_date) -> SampleDonorInterface:
        """Create the appropriate SampleDonor or SampleDonorMiabis object."""
        if self._miabis_on_fhir_model:
            return SampleDonorMiabis(identifier=identifier, gender=gender, birth_date=birth_date)
        else:
            return SampleDonor(identifier=identifier, gender=gender, birth_date=birth_date)

    def __build_donor(self, data: dict, is_validation: bool = False) -> SampleDonorInterface:
        validation_errors = [] if is_validation else None
        
        # Extract mandatory identifier
        identifier = str(data.get(self._donor_parsing_map.get("id")))
        
        # Parse gender (mandatory)
        gender = self.__parse_json_gender(data, identifier)
        
        # Parse optional birth date
        birth_date = self.__parse_json_birth_date(data, identifier, validation_errors)
        
        # If in validation mode and there are errors, raise them all together
        if is_validation and validation_errors:
            raise ExceptionGroup("Validation errors", validation_errors)
        
        # Create and return the appropriate donor object
        return self.__create_json_donor_object(identifier, gender, birth_date)
