import csv
import logging
import os
from typing import List, Generator

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

setup_logger()
logger = logging.getLogger()


class SampleDonorCsvRepository(SampleDonorRepository):
    """Class for handling sample donors stored in Csv files"""

    def __init__(self, records_path: str, separator: str, donor_parsing_map: dict, miabis_on_fhir_model: bool = False):
        self._dir_path = records_path
        self._ids: set = set()
        self.separator = separator
        self._donor_parsing_map = donor_parsing_map
        self._fields_dict = {}
        self._miabis_on_fhir_model = miabis_on_fhir_model
        logger.debug(f"Loaded the following donor parsing map {donor_parsing_map}")

    def get_all(self) -> Generator[SampleDonorInterface,None,None]:
        self._ids = set()
        dir_entry: os.DirEntry
        for dir_entry in os.scandir(self._dir_path):
            if dir_entry.name.lower().endswith(".csv"):
                yield from self.__extract_donor_from_csv_file(dir_entry)

    def __extract_donor_from_csv_file(self, dir_entry: os.DirEntry) -> SampleDonorInterface:
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

    def __build_donor(self, data: list[str]) -> SampleDonorInterface:
        identifier = data[self._fields_dict[self._donor_parsing_map.get("id")]]
        gender_field = self._fields_dict[self._donor_parsing_map.get("gender")]
        if gender_field is None:
            raise ValueError(f"No gender provided for patient with identifier {identifier}")
        if len(data[gender_field]) != 1:
            try:
                if self._miabis_on_fhir_model:
                    gender = MiabisGender[data[gender_field].upper()]
                else:
                    gender = ModuleGender[data[gender_field].upper()]
            except (ValueError, KeyError):
                if self._miabis_on_fhir_model:
                    gender = MiabisGender.UNKNOWN
                else:
                    gender = ModuleGender.UNKNOWN
        else:
            gender = miabis_get_gender_from_abbreviation(data[gender_field])
        birth_date_field = self._fields_dict[self._donor_parsing_map.get("birthDate")]
        date_of_birth = None
        if birth_date_field is not None:
            try:
                birth_date = date_parser.parse(data[birth_date_field])
                date_of_birth = birth_date
            except ParserError:
                raise ParserError(f"Error while parsing donor with identifier {identifier}. "
                                  f"Incorrect parsing date {data[birth_date_field]}. Please make sure the date is in a valid format.")
        if self._miabis_on_fhir_model:
            donor = SampleDonorMiabis(identifier=identifier, gender=gender, birth_date=date_of_birth)
        else:
            donor = SampleDonor(identifier=identifier, gender=gender, birth_date=date_of_birth)
        return donor

