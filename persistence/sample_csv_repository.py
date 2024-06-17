import csv
import logging
import os
from typing import Generator

from exception.wrong_sample_format import WrongSampleMapException
from model.sample import Sample
from persistence.sample_repository import SampleRepository
from util.custom_logger import setup_logger
from util.enums_util import parse_storage_temp_from_code

from persistence.csv_util import check_sample_map_format

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
                for row in reader:
                    sample = Sample(identifier=row[fields_dict[self._sample_parsing_map.get("sample_details").get("id")]],
                                    donor_id=row[fields_dict[self._sample_parsing_map.get("donor_id")]],
                                    material_type=row[fields_dict[self._sample_parsing_map.get("sample_details").get("material_type")]],
                                    diagnosis=self.__extract_first_diagnosis(self, row[fields_dict[self._sample_parsing_map
                                                                             .get("sample_details").get("diagnosis")]]))
                    if self._type_to_collection_map is not None:
                        sample.sample_collection_id = self._type_to_collection_map.get(sample.diagnosis)
                    if self._storage_temp_map is not None:
                        parsed_storage_temp = parse_storage_temp_from_code(self._storage_temp_map,
                                                                                 row[fields_dict[self._sample_parsing_map
                                                                                                 .get("sample_details")
                                                                                                 .get("storage_temperature")]])
                        if parsed_storage_temp is not None:
                            sample.storage_temperature = parsed_storage_temp
                    yield sample
            except WrongSampleMapException:
                logger.info("Given Sample map has a bad format, cannot parse the file")
                pass
            except TypeError as err:
                logger.info(err)
                pass

    @staticmethod
    def __extract_first_diagnosis(self, diagnosis_str: str):
        """Extracts only the first diagnosis, if the file has multiple diagnosis"""
        if ',' in diagnosis_str:
            return diagnosis_str.split(',')[0].strip()
        else:
            return diagnosis_str.strip()
