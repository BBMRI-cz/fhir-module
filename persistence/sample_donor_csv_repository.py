import csv
import logging
import os
from typing import Callable, Generator

from dateutil.parser import ParserError

from model.gender import Gender as ModuleGender
from miabis_model import Gender as MiabisGender
from model.interface.sample_donor_interface import SampleDonorInterface
from util.enums_util import get_gender_from_abbreviation
from model.sample_donor import SampleDonor
from model.miabis.sample_donor_miabis import SampleDonorMiabis
from miabis_model.gender import get_gender_from_abbreviation as miabis_get_gender_from_abbreviation
from persistence.sample_donor_repository import SampleDonorRepository
from util.custom_logger import setup_logger
from dateutil import parser as date_parser
from util.config import get_csv_separator

setup_logger()
logger = logging.getLogger()


class SampleDonorCsvRepository(SampleDonorRepository):
    """Class for handling sample donors stored in Csv files"""

    def __init__(self, records_path: str, separator: str, donor_parsing_map: dict, miabis_on_fhir_model: bool = False):
        super().__init__(records_path)
        self._ids: set = set()
        self.separator = separator
        self._donor_parsing_map = donor_parsing_map
        self._fields_dict = {}
        self._miabis_on_fhir_model = miabis_on_fhir_model
        logger.debug(f"Loaded the following donor parsing map {donor_parsing_map}")

    def get_all(self) -> Generator[SampleDonorInterface, None, None]:
        self._ids = set()
        with os.scandir(self._dir_path) as entries:
            for dir_entry in entries:
                if dir_entry.name.lower().endswith(".csv"):
                    yield from self.__extract_donor_from_csv_file(dir_entry)

    def update_mappings(self) -> None:
        """Update the mappings for the repository."""
        super().update_mappings()
        self._separator = get_csv_separator()

    def _get_supported_extensions(self) -> tuple[str, Callable]:
        return ".csv", self.__validate_donor_from_csv_file
    
    def __extract_donor_from_csv_file(self, dir_entry: os.DirEntry) -> SampleDonorInterface:
        try:
            with open(dir_entry, "r") as file_content:
                reader = csv.reader(file_content, delimiter=self.separator)
                self._fields_dict = {}
                fields = next(reader)
                for i, field in enumerate(fields):
                    self._fields_dict[field] = i
                for row in reader:
                    try:
                        donor = self.__build_donor(row)
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
            logger.debug(f"Error while opening file {dir_entry.name}. error: {e}")
            logger.info(f"Error while opening file {dir_entry.name} [Skipping...]")
            return
        
    def __validate_donor_from_csv_file(self, dir_entry: os.DirEntry) -> list[str]:
        errors = []
        try:
            with open(dir_entry, "r") as file_content:
                reader = csv.reader(file_content, delimiter=self.separator)
                self._fields_dict = {}
                fields = next(reader)
                for i, field in enumerate(fields):
                    self._fields_dict[field] = i
                row_index = 1  # Start from 1 since we skip header row
                for row in reader:
                    try:
                        donor = self.__build_donor(row, is_validation=True)
                        if donor.identifier not in self._ids:
                            self._ids.add(donor.identifier)
                    except ExceptionGroup as eg:
                        for exc in eg.exceptions:
                            errors.append(f"File {dir_entry.name} - Sample Donor (row {row_index}): {exc}")
                    except (ValueError, TypeError, KeyError) as err:
                        errors.append(f"File {dir_entry.name} - Sample Donor (row {row_index}): {err}")
                    finally:
                        row_index += 1
        except OSError as e:
            errors.append(f"Error while opening file {dir_entry.name}. error: {e}")
            return errors
        
        return errors


    def __parse_gender(self, data: list[str], identifier: str):
        """Parse and validate the gender field."""
        gender_field = self._fields_dict[self._donor_parsing_map.get("gender")]
        if gender_field is None:
            raise ValueError(f"No gender provided for patient with identifier {identifier}")
        
        gender_value = data[gender_field]
        
        # If it's a single character, treat it as an abbreviation
        if len(gender_value) == 1:
            return miabis_get_gender_from_abbreviation(gender_value)
        
        # Otherwise, try to parse it as a full gender name
        try:
            if self._miabis_on_fhir_model:
                return MiabisGender[gender_value.upper()]
            else:
                return ModuleGender[gender_value.upper()]
        except (ValueError, KeyError):
            if self._miabis_on_fhir_model:
                return MiabisGender.UNKNOWN
            else:
                return ModuleGender.UNKNOWN

    def __parse_birth_date(self, data: list[str], identifier: str, validation_errors: list | None):
        """Parse the optional birth date field."""
        birth_date_path = self._donor_parsing_map.get("birthDate")
        if birth_date_path is None:
            return None
        
        birth_date_field = self._fields_dict.get(birth_date_path)
        if birth_date_field is None:
            return None
        
        try:
            return date_parser.parse(data[birth_date_field])
        except ParserError:
            exception = ParserError(
                f"Error while parsing donor with identifier {identifier}. "
                f"Incorrect parsing date {data[birth_date_field]}. "
                f"Please make sure the date is in a valid format."
            )
            if validation_errors is not None:
                validation_errors.append(exception)
            else:
                raise exception
        
        return None

    def __create_donor_object(self, identifier: str, gender, date_of_birth) -> SampleDonorInterface:
        """Create the appropriate SampleDonor or SampleDonorMiabis object."""
        if self._miabis_on_fhir_model:
            return SampleDonorMiabis(identifier=identifier, gender=gender, birth_date=date_of_birth)
        else:
            return SampleDonor(identifier=identifier, gender=gender, birth_date=date_of_birth)

    def __build_donor(self, data: list[str], is_validation: bool = False) -> SampleDonorInterface:
        validation_errors = []
        
        # Extract mandatory identifier
        identifier = data[self._fields_dict[self._donor_parsing_map.get("id")]]
        
        # Parse gender (mandatory)
        gender = self.__parse_gender(data, identifier)
        
        # Parse optional birth date
        date_of_birth = self.__parse_birth_date(data, identifier, validation_errors)
        
        # If in validation mode and there are errors, raise them all together
        if is_validation and validation_errors:
            raise ExceptionGroup("Validation errors", validation_errors)
        
        # Create and return the appropriate donor object
        return self.__create_donor_object(identifier, gender, date_of_birth)
