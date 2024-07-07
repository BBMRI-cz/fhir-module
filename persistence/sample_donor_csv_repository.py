import csv
from datetime import datetime
import logging
import os
from typing import List

from util.enums_util import get_gender_from_abbreviation
from model.sample_donor import SampleDonor
from persistence.sample_donor_repository import SampleDonorRepository
from util.custom_logger import setup_logger

setup_logger()
logger = logging.getLogger()


class SampleDonorCsvRepository(SampleDonorRepository):
    """Class for handling sample donors stored in Csv files"""

    def __init__(self, records_path: str, separator: str, donor_parsing_map: dict):
        self._dir_path = records_path
        self._ids: set = set()
        self.separator = separator
        self._donor_parsing_map = donor_parsing_map
        logger.debug(f"Loaded the following donor parsing map {donor_parsing_map}")

    def get_all(self) -> List[SampleDonor]:
        dir_entry: os.DirEntry
        for dir_entry in os.scandir(self._dir_path):
            if dir_entry.name.lower().endswith(".csv"):
                yield from self.__extract_donor_from_csv_file(dir_entry)

    def __extract_donor_from_csv_file(self, dir_entry: os.DirEntry) -> SampleDonor:
        fields_dict: dict = {}
        with open(dir_entry, "r") as file_content:
            reader = csv.reader(file_content, delimiter=self.separator)
            fields = next(reader)
            for i, field in enumerate(fields):
                fields_dict[field] = i
            for row in reader:
                try:
                    donor = SampleDonor(row[fields_dict[self._donor_parsing_map.get("id")]])
                    donor.gender = get_gender_from_abbreviation(row[fields_dict[self._donor_parsing_map.get("gender")]])
                    year_of_birth = row[fields_dict[self._donor_parsing_map.get("birthDate")]]
                    if year_of_birth is not None:
                        try:
                            parsed_date = datetime.strptime(year_of_birth, "%d.%m.%Y")
                        except ValueError:
                            parsed_date = datetime.strptime(year_of_birth, "%Y")
                        donor.date_of_birth = parsed_date
                    if donor.identifier not in self._ids:
                        self._ids.add(donor.identifier)
                        yield donor
                except TypeError as e:
                    logger.info(e, "Skipping...")
                    return


