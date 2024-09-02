import csv
import logging
import os
import re
from typing import Generator

from dateutil.parser import ParserError

from exception.wrong_sample_format import WrongSampleMapException
from model.sample import Sample
from persistence.sample_repository import SampleRepository
from util.custom_logger import setup_logger
from util.enums_util import parse_storage_temp_from_code

from persistence.csv_util import check_sample_map_format

from dateutil import parser as date_parser

setup_logger()
logger = logging.getLogger()


class SampleCsvRepository(SampleRepository):
    """Class for handling persistence in Csv files"""

    def __init__(self, records_path: str, sample_parsing_map: dict, separator: str,
                 type_to_collection_map: dict = None, storage_temp_map: dict = None):
        self._dir_path = records_path
        self._sample_parsing_map = sample_parsing_map
        self._separator = separator
        logger.debug(f"Loaded the following sample parsing map {sample_parsing_map}")
        self._type_to_collection_map = type_to_collection_map
        self._storage_temp_map = storage_temp_map

    def get_all(self) -> Generator[Sample, None, None]:
        dir_entry: os.DirEntry
        for dir_entry in os.scandir(self._dir_path):
            if dir_entry.name.lower().endswith(".csv"):
                yield from self.__extract_sample_from_csv_file(dir_entry)

    def __extract_sample_from_csv_file(self, dir_entry: os.DirEntry) -> Sample:
        fields_dict: dict = {}
        with open(dir_entry, "r") as file_content:
            reader = csv.reader(file_content, delimiter=self._separator)
            fields = next(reader)
            for i, field in enumerate(fields):
                fields_dict[field] = i
            try:
                check_sample_map_format(self._sample_parsing_map)
            except WrongSampleMapException:
                logger.info("Given Sample map has a bad format, cannot parse the file")
                return
            for row in reader:
                try:
                    sample = Sample(
                        identifier=row[fields_dict[self._sample_parsing_map.get("sample_details").get("id")]],
                        donor_id=row[fields_dict[self._sample_parsing_map.get("donor_id")]])
                    material_type_field = fields_dict.get(
                        self._sample_parsing_map.get("sample_details").get("material_type"))
                    diagnosis_field = fields_dict.get(self._sample_parsing_map.get("sample_details").get("diagnosis"))

                    storage_temp_field = fields_dict.get(self._sample_parsing_map
                                                         .get("sample_details")
                                                         .get("storage_temperature"))

                    collection_date_field = fields_dict.get(self._sample_parsing_map
                                                            .get("sample_details")
                                                            .get("collection_date"))
                    if material_type_field is not None:
                        sample.material_type = row[material_type_field]
                    if diagnosis_field is not None:
                        sample.diagnoses = self.__extract_all_diagnosis(row[diagnosis_field])
                    if collection_date_field is not None:
                        try:
                            sample.collected_datetime = date_parser.parse(row[collection_date_field]).date()
                        except ValueError:
                            logger.warning(
                                f"Error parsing date {row[collection_date_field]}. Please make sure the date is in a valid format.")
                            continue
                    if self._type_to_collection_map is not None:
                        sample.sample_collection_id = None
                        attribute_to_collection = self._sample_parsing_map.get("sample_details").get("collection")
                        if attribute_to_collection in fields_dict:
                            sample.sample_collection_id = self._type_to_collection_map.get(
                                row[fields_dict[attribute_to_collection]])
                    if self._storage_temp_map is not None and storage_temp_field is not None:
                        parsed_storage_temp = parse_storage_temp_from_code(
                            self._storage_temp_map,
                            row[storage_temp_field])
                        if parsed_storage_temp is not None:
                            sample.storage_temperature = parsed_storage_temp
                    yield sample

                except ParserError:
                    logger.warning(
                        f"Error parsing date {row[collection_date_field]}. Please make sure the date is in a valid format.")
                    continue
                except TypeError as err:
                    logger.info(f"{err} Skipping....")
                    continue
                except ValueError as err:
                    logger.info(f"{err} Skipping....")
                    continue

    @staticmethod
    def __extract_all_diagnosis(diagnosis_str: str) -> list[str]:
        """Extract all diagnosis from a string"""
        pattern = r'\b[A-Z][0-9]{2}(?:\.)?(?:[0-9]{1,2})?\b'
        return re.findall(pattern, diagnosis_str)
